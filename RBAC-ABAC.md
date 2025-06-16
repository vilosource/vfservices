Designing a Scalable ABAC/RBAC System in a Django Microservices Architecture
Introduction
Implementing fine-grained authorization in a microservices environment is challenging but achievable with a careful design. In a Django-based microservices architecture, we want to combine Role-Based Access Control (RBAC) with Attribute-Based Access Control (ABAC) to enforce both coarse-grained role permissions and context-specific rules. The goal is to centralize identity data while distributing authorization logic to each service – a balance that avoids a monolithic policy service becoming a development bottleneck
osohq.com
alexanderlolis.com
. We will design a solution following SOLID principles and using proven design patterns (Strategy, Registry, Dependency Injection, Template Method) to ensure the system is modular, extensible, and testable. Core architecture components:
Minimal JWTs: Authentication tokens carry only a user identifier (sub) and expiration (exp), nothing more. This avoids embedding roles/attributes in tokens, which can bloat token size or become stale
osohq.com
. Instead, services will fetch the latest roles/attributes on each request as needed.
Redis as Central Attribute Store: A fast in-memory data store (Redis) holds user attributes and role assignments, namespaced per service. This serves as a Policy Information Point (PIP) cache for all services, enabling quick lookup of a user’s roles/attributes without repeated database queries. The authorization service (Identity Provider) populates Redis so that microservices can read from it with minimal latency. Storing roles in a central store like Redis is a known practice for improving performance in microservices
stackoverflow.com
.
Service Manifest Registration: Each microservice declares its authorization metadata via a manifest (e.g. JSON or YAML) at deploy time. The manifest specifies the service’s name, the roles it supports (scoped to that service), and any custom user attributes it uses for ABAC decisions. The Identity Provider (IDP) ingests this manifest to register the service’s roles and attributes in a database or config, ensuring a single source of truth for all roles. This registration process is idempotent – services can repeatedly register on deployment without creating duplicates, allowing scalable and automated updates.
Central ABAC Policy Definitions: ABAC policies are defined as reusable functions that encapsulate complex permission logic (for example, an ownership check or admin override). These policy functions are registered in a policy registry via a decorator, acting as a centralized catalogue of authorization rules. By centralizing policy definitions (e.g. in a shared library), multiple services can reuse common patterns (such as “owner of object or admin of group can edit”) and remain consistent. The registry pattern lets us add new policy rules easily without modifying the code that uses them – we just register a new function, and it becomes available by name (Open/Closed principle).
Django Model Integration (ABACModelMixin): Domain models in each service include an ABACModelMixin that provides a generic check_abac() method. This method delegates the permission check to the appropriate policy function from the registry, given the current user’s attributes and the desired action. The mixin approach keeps authorization logic out of the core model code (Single Responsibility) and allows using a Template Method pattern – the mixin defines the high-level check_abac algorithm, while specific models can override or provide data (like which policy to use or which object fields represent ownership) as needed.
Queryset Filtering (.abac_filter()): To handle list APIs efficiently, custom Django QuerySet methods apply ABAC rules at the database query level. Instead of fetching all objects and filtering in Python (which would be unscalable), .abac_filter(user_attrs, action) adds query constraints based on the user’s attributes and roles. For example, an ABAC rule like “user can view a document if they are the owner or in the document’s group as an admin” can be translated into a Q filter (owner_id = user OR group_id in user’s admin group list) and applied in the database query. This prevents over-fetching data the user isn’t allowed to see
stackoverflow.com
stackoverflow.com
. When a policy is too complex to fully translate to a query, the method can fall back to a safer default (e.g. return none or do post-filtering on a smaller candidate set), but the aim is to push as much filtering to the DB as possible for performance.
Below, we delve into each of these components and how to implement them in a SOLID-compliant way, with code examples and design pattern usage.
JWT and Attribute Retrieval via Redis
In this architecture, JWTs issued by the IDP are kept minimal – essentially acting as authentication tokens carrying the user’s ID. All authorization data (roles, group memberships, etc.) is kept outside the token, which avoids issues of tokens becoming too large or containing stale permissions
osohq.com
. When a request hits a microservice, the service uses the JWT’s sub (user ID) to retrieve that user’s attributes and roles from Redis. Why Redis? Redis serves as a distributed cache accessible by all services, providing millisecond latency lookups. By keeping user-role mappings in memory, we avoid hitting a central database or IDP on every request. This aligns with the microservice authorization pattern of “leaving the data where it is and having services ask for it when needed,” with the twist that here “where it is” is a fast cache
osohq.com
osohq.com
. Each service knows how to key into Redis for its scope. For example, a key scheme might be:
user:{user_id}:roles:{service_name} – stores the list of role names the user has for that service (global roles or resource-scoped roles relevant to that service).
user:{user_id}:attrs:{service_name} – stores a hash of attribute names to values that the service’s policies might use (or a combined single hash for roles and attrs).
When a request comes in, the service loads the user’s attribute profile with a simple call, e.g.:
python
Copy
def get_user_attributes(user_id, service_name):
    key = f"user:{user_id}:attrs:{service_name}"
    data = redis_client.hgetall(key)
    return UserAttributes(**data)  # perhaps map to a dataclass for convenience
This UserAttributes object can contain both role information (e.g. roles = ['editor', 'admin']) and other attributes (e.g. department = 'Sales', admin_group_ids = [5, 7], etc.). The Dependency Injection (DI) principle is applied here by not hard-coding the Redis access throughout the codebase – we could inject the redis_client (or an abstraction of it) into functions or classes that need it, making it easy to replace with a mock for tests or swap out the storage backend if needed. For instance, a service could have a RoleAttributeService class that takes a cache client in its constructor (inverting the dependency on a concrete Redis client). This ensures our business logic (the policy checks) depend on an abstract data provider interface, not a concrete Redis instance (adhering to dependency inversion). Caching and Invalidation: By centralizing role data in Redis, we must consider how to keep it in sync with ground truth (which might be an underlying database or admin actions in the IDP). The IDP should update the Redis cache whenever a user’s roles or relevant attributes change – for example, if an admin revokes a role, the IDP service would delete or update the corresponding Redis key for that user. To propagate changes that might be cached in-memory in each service process, a publish/subscribe strategy can be used: the IDP publishes an invalidation message (e.g. “user 42 roles updated”) on a Redis Pub/Sub channel, and each microservice instance subscribes to that channel to know it should evict or refresh that user’s cache entry. This pattern ensures all services see updates nearly instantly and prevents serving stale permissions
redis.io
. In practice, one can leverage Redis keyspace notifications or a messaging broker similarly, but using Redis Pub/Sub keeps the solution self-contained in Redis. Additionally, to be safe, the microservices can enforce a short TTL on cached data (e.g. a few minutes) so that even if an invalidation message is missed (network glitch, etc.), the data will naturally refresh periodically. This approach – combining on-demand fetch, Pub/Sub invalidation
redis.io
, and TTL – yields a robust caching strategy that scales to many services without constant database reads.
Service Manifest and Idempotent Registration
On deployment, each microservice registers itself with the Identity Provider by sending a manifest describing its authorization requirements. This manifest-driven approach makes adding or updating services straightforward and avoids hardcoding new roles or permissions into the IDP (which would violate open/closed and require frequent changes). Instead, the IDP treats manifests as data, not code. Manifest contents: At minimum, the manifest contains:
Service Name or ID: A unique identifier for the service (used as a namespace for roles/attributes).
Roles: A list of roles that the service recognizes, possibly with descriptions and whether they are global or scoped to specific resources. For example, a document_service might declare roles like document_admin (global role giving admin rights in that service), editor (maybe scoped to particular documents or projects), etc.
User Attributes: Any additional user attributes this service will expect in Redis for ABAC decisions. These could be global user attributes (like department, clearance level) or service-specific ones (like a list of project IDs the user is assigned to). Declaring them ensures the IDP knows to collect or maintain these attributes for each user.
An example manifest (as JSON) for a hypothetical Document service:
json
Copy
{
  "service": "document_service",
  "roles": [
    {"name": "document_admin", "description": "Full access to all documents"},
    {"name": "editor", "description": "Can edit documents in their department"},
    {"name": "viewer", "description": "Can view assigned documents"}
  ],
  "attributes": [
    {"name": "department", "description": "User department, used for ABAC policies"},
    {"name": "assigned_doc_ids", "description": "List of document IDs the user can access"}
  ]
}
Upon receiving this, the IDP will:
Upsert the Service Record: If document_service is new, create a new entry; if it exists, update its metadata.
Upsert Roles: For each role, either create it (scoped under this service) or update the description if it already exists. Roles can be stored in a table with columns like (service, role_name, description). Idempotency means if the manifest is sent again, the operation results in the same final state (duplicate roles are not re-created, nothing is broken by re-registration). This can be done by using database upsert operations or checking for existence before insert.
Register Attributes: Ensure the IDP’s user attribute schema can accommodate the new attributes. For example, the IDP might maintain a list of known attribute keys per service and merge any new ones. If using a schemaless store like Redis or a JSON column, this might just be informational. In other cases, it could mean adding new columns to a profile DB or updating a schema in a NoSQL store.
This manifest approach makes adding a new service or new model permissions a data operation, not a code change on the IDP. The core IDP logic (e.g., issuing tokens, storing user data) remains unchanged when new services come online. We avoid the central authorization service needing to know every domain’s details in its code
osohq.com
. In effect, the IDP just becomes a registry of services/roles and a repository of user-role assignments, not a hard-coded policy engine. This adheres to the Open/Closed Principle: the system is open to new services and permission types, but the IDP’s code is closed to modification for each new addition. Finally, the manifest can also trigger the IDP to allocate any needed Redis structures for the service. For example, if a new service is registered, the IDP might initialize empty role sets or attribute fields for all existing users (or do so lazily on first access). In practice, one might simply handle this lazily: when a new attribute is requested by a service but not set for a user, it defaults to empty/null.
Defining ABAC Policies with Strategy and Registry Patterns
A cornerstone of ABAC is the policy – the rule that decides if a given action on a resource is allowed for a user with certain attributes. We design policies as Python functions (or small callable objects) that encapsulate these rules. Using the Strategy pattern, each policy is essentially a pluggable strategy for authorization that can be selected by name. We use a Registry to keep track of available policies, mapping string identifiers to the actual functions. This design allows us to separate policy logic from models and from the enforcement code: policies can be written and tested in isolation, and new policies can be introduced without modifying the code that looks them up. To implement the registry, we can use a simple dictionary and a decorator for registration:
python
Copy
# Global registry for ABAC policy functions
POLICY_REGISTRY = {}

def register_policy(name):
    """Decorator to register an ABAC policy function by name."""
    def decorator(func):
        POLICY_REGISTRY[name] = func
        return func
    return decorator

# Example policy definitions:

@register_policy('default_ownership_group_admin')
def default_ownership_group_admin(user_attrs, obj=None, action=None):
    """
    Allow action if the user is the owner of the object or an admin of the object's group.
    Assumes obj has attributes `owner_id` and `group_id`, and user_attrs has `user_id` and `admin_group_ids`.
    """
    if obj is None:
        return False  # No object to check against
    # Check if user is the owner
    if hasattr(obj, 'owner_id') and obj.owner_id == user_attrs.user_id:
        return True
    # Check if user is admin of the group that this object belongs to
    if hasattr(obj, 'group_id') and obj.group_id in getattr(user_attrs, 'admin_group_ids', []):
        return True
    return False

@register_policy('departmental_editor')
def departmental_editor(user_attrs, obj=None, action=None):
    """
    Allow if user's department matches the object's department attribute, or user has an admin role.
    """
    if obj is None:
        return False
    if hasattr(obj, 'department') and hasattr(user_attrs, 'department'):
        if obj.department == user_attrs.department:
            return True
    # Also allow if user has a role of document_admin in this service (role could be stored in user_attrs.roles)
    if 'document_admin' in getattr(user_attrs, 'roles', []):
        return True
    return False
In the above example, we defined two policies and registered them in the POLICY_REGISTRY by using the @register_policy decorator. The default_ownership_group_admin policy implements a common pattern: owners or group admins can perform certain actions. The second policy departmental_editor illustrates combining an attribute (department) with a role check. These are simplistic for demonstration, but real policies could consider any number of attributes (time of day, object state, etc.). Using Strategy pattern: Each policy function is a strategy (an algorithm deciding authorization) that can be swapped out. By calling through the registry, the code using these policies doesn’t hardcode which logic to run – it selects by name, or even dynamically by configuration. This makes the system flexible; for example, if a new type of rule is needed (say, based on project membership), one can add a new function for it and register it, without altering the core enforcement mechanism. It also promotes Single Responsibility: each policy function handles one specific rule or combination of conditions. Open for extension: Adding a new policy is as easy as writing a new decorated function. The registry and the rest of the system do not need modification to accommodate it – they’ll pick it up by name. This aligns with the Open/Closed principle and makes the authorization system adaptable to new requirements (new models might come with new policy needs). To ensure policy functions remain SOLID, we should keep them pure (calculating a decision from inputs, without side effects). They receive all needed data via parameters (user attributes, object, action) rather than, say, querying the database or global state internally. This makes them predictable and testable in isolation. If a policy does need extra data (like looking up a hierarchy), that should be abstracted – for example, if checking “manager of user X can edit X’s data,” and the manager relationships are not already in attributes, we might either expand the attributes provided to include managed_user_ids or have the policy call a domain method. In general, complex logic might be better handled by preparing attributes in advance (e.g., IDP could include a list of subordinates for a user if needed for policies), so that policy functions remain straightforward boolean logic.
ABACModelMixin and Django ORM Integration
To integrate these policies with Django models, we introduce an ABACModelMixin that model classes can subclass. This mixin provides a generic implementation of permission checks by delegating to the policy registry, and allows models to specify which policy applies for which action. This is an application of the Template Method pattern: the base mixin defines the workflow of checking a permission, but the exact policy name or conditions can be supplied by the subclass (or even determined at runtime based on model data). Defining the mixin:
python
Copy
class ABACModelMixin:
    # Each model can define a mapping of action -> policy name to use for that action.
    # For example: {'view': 'default_ownership_group_admin', 'edit': 'departmental_editor'}
    ABAC_POLICIES = {}  # class attribute expected in subclasses

    def check_abac(self, user_attrs, action):
        """Check if the given user (described by user_attrs) is allowed to perform action on this object."""
        policy_name = None
        # First, see if the model class defines a policy for this action
        if action and hasattr(self.__class__, 'ABAC_POLICIES'):
            policy_name = self.ABAC_POLICIES.get(action)
        if not policy_name:
            return False  # No policy defined for this action, default deny (could also default allow if desired).
        # Look up the policy function in the registry
        policy_func = POLICY_REGISTRY.get(policy_name)
        if policy_func is None:
            # Policy not found in registry (misconfiguration) – secure default is to deny.
            return False
        # Call the policy with user attributes and this object
        return bool(policy_func(user_attrs, obj=self, action=action))
With this mixin, any Django model can easily get ABAC behavior by specifying its policy names. For example:
python
Copy
class Document(ABACModelMixin, models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    department = models.CharField(max_length=50)
    # Define which ABAC policy to use for certain actions
    ABAC_POLICIES = {
        'view': 'default_ownership_group_admin',      # owners or group admins can view
        'edit': 'departmental_editor'                 # only same-department or admin can edit
    }
    # ... other fields ...
Now Document inherits check_abac. If in a view or business logic we have a doc instance and want to verify a user can edit it, we do: allowed = doc.check_abac(user_attrs, action='edit'). The mixin will find that 'edit' maps to 'departmental_editor', retrieve that function, and invoke it with user_attrs and doc. The policy function then applies the logic we defined earlier. The Template Method pattern is evident: check_abac in the base class outlines the steps (find policy name, lookup function, execute it), while the subclass (the concrete model) supplies the specifics (which policy name for a given action). If a model has very custom logic that doesn’t fit a reusable policy, it can always override check_abac itself to implement special cases. But in most cases, we aim to reuse common policies. This division makes our models lightweight – they don’t implement permission logic internally (just reference a named policy). It also means changes to policy logic (e.g. tweaking what “group admin” means) are done in one place in the policy function, rather than in every model or view that needs it (DRY principle). Custom QuerySet for ABAC filtering: For list views or any bulk access, evaluating check_abac on each object individually would be inefficient. We leverage Django’s ability to customize QuerySet behavior via a Manager. We can create a QuerySet subclass that includes an abac_filter method to automate filtering based on a given action and user attributes. For example:
python
Copy
from django.db.models import Q, QuerySet

class ABACQuerySet(QuerySet):
    def abac_filter(self, user_attrs, action):
        """Filter the queryset to only include objects where user_attrs is allowed to perform 'action'."""
        model_cls = self.model
        if not hasattr(model_cls, 'ABAC_POLICIES'):
            return self.none()  # If the model doesn't define ABAC policies, deny by default.
        policy_name = model_cls.ABAC_POLICIES.get(action)
        if not policy_name:
            return self.none()
        # Try to apply known patterns as database filters for efficiency:
        if policy_name == 'default_ownership_group_admin':
            # Example: translate the 'owner or group admin' rule into a Q object
            q = Q()
            if hasattr(user_attrs, 'user_id'):
                q |= Q(owner_id=user_attrs.user_id)
            if hasattr(user_attrs, 'admin_group_ids'):
                q |= Q(group_id__in=user_attrs.admin_group_ids)
            return self.filter(q)
        elif policy_name == 'departmental_editor':
            q = Q()
            # Filter by same department
            if getattr(user_attrs, 'department', None):
                q |= Q(department=user_attrs.department)
            # If user has an admin role for this service, they can access all (skip filtering)
            if 'document_admin' in getattr(user_attrs, 'roles', []):
                return self  # no filtering; admin sees all
            return self.filter(q)
        else:
            # Fallback: no optimized filter, so we must check each object (note: this pulls all objects!)
            # In practice, avoid this by defining filter logic for each common policy.
            allowed_ids = []
            for obj in self:
                if obj.check_abac(user_attrs, action):
                    allowed_ids.append(obj.pk)
            return self.filter(pk__in=allowed_ids)
This example shows how we can implement .abac_filter for the two known policies. For default_ownership_group_admin, it builds a Q object that filters by owner or by group membership. For departmental_editor, it filters by department and checks a role for full access. If the policy is unrecognized, it falls back to checking each object (which is not ideal for large querysets – so in production we’d ensure each policy we use frequently has a translation or we restructure queries differently). Using this custom QuerySet requires hooking it into the model’s manager. For instance:
python
Copy
class DocumentManager(models.Manager):
    def get_queryset(self):
        return ABACQuerySet(self.model, using=self._db)

class Document(ABACModelMixin, models.Model):
    # ... fields ...
    objects = DocumentManager()
    ABAC_POLICIES = { 'view': 'default_ownership_group_admin', 'edit': 'departmental_editor' }
Now Document.objects.abac_filter(user_attrs, 'view') will give a QuerySet already restricted to only the docs the user can view. This is extremely useful in a Django REST Framework ListAPI scenario. Why not centralize all ABAC checks in one service? We deliberately design the checks to happen within each service’s domain, close to its data. This avoids the need to ship potentially large lists of object IDs across the network for filtering, as a centralized PDP would have to do
stackoverflow.com
stackoverflow.com
. Each service knows how to enforce its own rules in an efficient manner (often at the SQL level). As Alexander Lolis noted, keeping authorization logic in each service, with a shared library of common code, is a good balance for scalability and maintainability
alexanderlolis.com
. We isolate rules to the service that owns the data, and just provide common tools (like the policy registry and mixin) to avoid reinventing the wheel in each service. Each service’s team can thus own their authorization rules (following Single Responsibility and high cohesion), and we reduce tight coupling to a central auth service.
Integration with Django REST Framework (DRF)
Integrating this system with DRF involves using the permissions system and viewset capabilities to enforce ABAC on API endpoints. There are two levels of checks to consider: general access (e.g., can the user call this endpoint at all?) and object-level access (can they access this specific object or subset of data?). Endpoint (view) level authorization: If certain endpoints require a user to have a specific role regardless of which object is accessed, we can use DRF’s BasePermission classes for a coarse check. For example, an endpoint that creates a new Project might require the user has a “project_creator” role. This can be done with a custom permission class that reads the user’s roles from Redis (via user_attrs) and checks for the presence of that role. Such checks are pure RBAC and could even be handled by a simpler mechanism (like encoding in the manifest that “role X can access endpoint Y”), but implementing as code in DRF is straightforward:
python
Copy
from rest_framework.permissions import BasePermission

class RoleRequired(BasePermission):
    def __init__(self, required_role):
        self.required_role = required_role

    def has_permission(self, request, view):
        user_attrs = get_user_attributes(request.user.id, service_name="project_service")
        return self.required_role in user_attrs.roles
We could then attach RoleRequired('project_creator') to the view’s permission_classes. However, many endpoints might not need such static role checks if the logic is entirely captured by ABAC on objects. Often, the “role” is just another attribute to consider in the ABAC policy for the object. For example, instead of requiring an “editor” role on the view, we could allow anyone to call the view, but in the list/queryset filter only return objects if they’re an editor for them. Both approaches can coexist: use broad RBAC checks for actions that clearly require a certain high-level role (e.g., only an “admin” can use a bulk delete endpoint), and use ABAC checks for fine-grained filtering and object permissions. Object-level authorization in DRF: DRF’s permission system has a hook for object-level checks: has_object_permission(self, request, view, obj). We can create a permission class that utilizes our model’s check_abac method for this. For example:
python
Copy
class ABACPermission(BasePermission):
    """
    A DRF permission that checks ABAC policies on a per-object basis using the model's check_abac.
    """
    def has_permission(self, request, view):
        # Optional: we could do a coarse check here (like ensure user is authenticated).
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Load user attributes from Redis for this service
        user_attrs = get_user_attributes(request.user.id, service_name=view.service_name)
        # Determine the action name. In ViewSets, we can map HTTP methods to actions or use view.action.
        action = getattr(view, 'action', None)
        if action is None:
            # Fallback: map method to action name, e.g. "GET" -> "view", "PUT" -> "edit", etc.
            if request.method in ("GET", "HEAD"):
                action = "view"
            elif request.method == "POST":
                action = "create"
            elif request.method == "PUT" or request.method == "PATCH":
                action = "edit"
            elif request.method == "DELETE":
                action = "delete"
        # Use the object's check_abac (from ABACModelMixin)
        if hasattr(obj, 'check_abac'):
            return obj.check_abac(user_attrs, action)
        return True  # If obj has no ABAC (like not using mixin), allow by default or handle elsewhere.
We attach this ABACPermission to any viewset that deals with ABAC-managed models. For example:
python
Copy
class DocumentViewSet(ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [ABACPermission]
    service_name = "document_service"  # used by ABACPermission to fetch attributes

    def get_queryset(self):
        # Even though object-level permission will filter individual objects on detail requests,
        # we also filter the list results at the query level:
        user_attrs = get_user_attributes(self.request.user.id, service_name=self.service_name)
        return Document.objects.abac_filter(user_attrs, action='view')
In the get_queryset, we call our abac_filter to ensure list responses only contain allowed objects. DRF will also call has_object_permission for each object in detail routes (and optionally for each item in list if configured, though not by default). By combining query filtering and per-object check, we have defense in depth: even if a developer forgets to filter the queryset, the ABACPermission ensures no forbidden object slips through in detail views or other routes. This approach cleanly separates concerns: the viewset doesn’t need to know the details of why a user can or cannot access an object – it delegates to the model’s check_abac (which in turn delegates to the policy logic). The view only needs to know when to enforce (e.g., on GET, use the filter; on object access, rely on permission check). Because we use a common library approach (the mixin, the permission class, the attribute loader), adding a new model or even a new service’s API requires minimal boilerplate. You’d create your Django model, assign ABAC_POLICIES, and create a ViewSet that uses ABACPermission and filters with .abac_filter() – no need to implement repetitive permission code. This reflects the DRY principle and the idea from Alexander Lolis that “common code [should be] implemented as a library (or libraries) since it will be shared among all services”
alexanderlolis.com
. We ensure every service uses the same battle-tested authorization library components, reducing errors and inconsistencies. One can further enhance integration by writing a DRF filter backend that automatically applies abac_filter based on the request and view context, or by writing a mixin for viewsets that does the same. Those are implementation conveniences – the core is that the heavy lifting is done by our model layer and policy functions.
Extensibility and SOLID Compliance
Our design emphasizes extensibility at every layer. Adding new services or models does not require modifying the central IDP logic or the shared authorization code – it’s largely a matter of configuration and using the existing patterns. Let’s recap how SOLID principles are addressed:
Single Responsibility Principle: Each component has a focused responsibility. The IDP manages identities and roles (and provides attributes) – it does not decide per-resource authorization. The policy functions decide if an action is allowed based on input attributes – they do not fetch data or perform other tasks. The models know how to call policy checks but not the details of the policies. This separation makes the system easier to maintain. For instance, if caching needs to change, we can modify how get_user_attributes works without touching the policy logic; if a policy logic changes, we update one function without affecting model code.
Open/Closed Principle: The registry and manifest approach mean we can extend the system with new policies, roles, attributes, and even entire new microservices, with minimal code changes to existing components. New roles are added via data (manifests) rather than code. New policies are added by registering new strategy functions, without altering the registry mechanism. New models utilize the existing mixin and thus don’t require changes to that mixin’s code. The authorization library is open for extension (via new plugins, policies) but closed for modification of its core. This prevents regression risk and centralizes necessary changes.
Liskov Substitution Principle: LSP is more about ensuring subclass substitutability. In our context, using ABACModelMixin does not violate LSP – a Document can be used wherever an ABACModelMixin is expected. We also ensure that our UserAttributes (which might be a simple data class or dict) presents a consistent interface to policies. Policies don’t care if user_attrs is a real object or a mock, as long as it has the needed attributes (duck typing), which is convenient for testing.
Interface Segregation Principle: We provide clean interfaces for each piece. The check_abac(user_attrs, action) is a simple interface for “can this user do X on this object.” Callers of check_abac (like the permission class) don’t need to know how it’s implemented. If some models needed a completely different way to check permissions, they could implement their own interface (but typically we’d unify on one). The IDP’s interface for manifests and for attribute retrieval is also clean – services just call get_user_attributes(user, service) and don’t worry if behind the scenes it’s Redis or something else. By not forcing modules to depend on things they don’t use, we keep each piece focused (for example, a service doesn’t need to interact with the roles database in IDP, it only cares about Redis and its own policies).
Dependency Inversion Principle: We inverted certain dependencies – for instance, policy evaluation in the service depends on abstract policy names and user data, not on concrete IDP calls. The IDP, in turn, doesn’t need to know about service internals; it just provides data. We could even imagine an abstract PolicyEngine interface that the mixin calls, which could be implemented by a local evaluator or a remote call – but here we chose local for performance. Nonetheless, because we funneled all checks through check_abac and POLICY_REGISTRY, if we ever needed to swap out the mechanism (say, use an external PDP like Oso or Open Policy Agent), we could do so by implementing check_abac differently or populating the registry with proxies that call that external service. The high-level code (views, etc.) wouldn’t change. Similarly, by treating Redis as an implementation detail of attribute storage (with an abstraction in front), we could change to another store or add a backing database without breaking how services ask for user attributes.
Scalability considerations: Each service is responsible for its own authorization enforcement, which distributes the load. No single auth service becomes a choke point on each request (a central PDP would have to handle every permission check in the system). Instead, the IDP is only involved in authentication and in updating/distributing attributes. This improves reliability – if the IDP is briefly down, services can continue to use cached roles from Redis for a time (assuming JWTs are valid), and a failure in one service’s auth logic doesn’t directly impact others. However, we are still maintaining consistent central data for roles, which is crucial for admin oversight. The IDP remains the one place to, say, remove a role from a user – and that revocation propagates to all services via the cache. This design is in line with the idea of centralizing data but federating decision-making, avoiding the extremes of fully central PDP or fully siloed auth. For teams adding new microservices, the process is streamlined: define your roles and any special attributes, write any new policy functions or reuse existing ones, include the common auth library, and declare your model’s ABAC rules. You don’t have to touch the IDP’s code or the other services. The new service will register itself and start participating in the ecosystem. This modular approach supports a growing system without constant refactoring of a central auth module. As noted in industry discussions, a homogeneous approach using a shared library per service can work well, especially if all services are in the same tech stack
alexanderlolis.com
 (here, Python/Django) – we implemented everything once and share it, rather than having to re-implement in each service from scratch.
Conclusion
By combining RBAC’s simplicity (role checks) with ABAC’s flexibility (attribute-driven rules), and by leveraging Django’s strengths, we designed an authorization system that is both powerful and maintainable. Key to this design is the use of design patterns: Strategy (pluggable policy algorithms), Registry (central lookup of policies), Template Method (generic model permission checks with hook for specifics), and judicious Dependency Injection (for caches and policy data). The system ensures consistent enforcement across microservices while avoiding a monolithic “God service” that must know every detail of every service’s data model
osohq.com
. Instead, each service is the master of its own domain’s rules, using a common framework. This architecture addresses the performance pitfalls of naive ABAC in microservices (like fetching thousands of records and filtering in memory
stackoverflow.com
) by pushing filtering to the database and caching what’s needed in memory. It also aligns with best practices like using centralized identity data but local decision making for scalability
alexanderlolis.com
. In practice, one should accompany this design with thorough testing of each policy and careful management of the Redis cache (ensuring security of that cache, as it now contains authorization info). Audit logging can be added at the policy decision points (e.g., log whenever check_abac denies an access) to have traceability. Overall, the result is an extensible, scalable authorization system for Django microservices that upholds SOLID principles, making it easier to grow and maintain in the long run. By planning for new additions (services, roles, policies) as first-class data/configuration, we future-proof the IDP and keep the complexity at the edges (where the domain knowledge is), rather than in the center. This approach keeps our security logic clean, testable, and adaptable to change – crucial attributes for any system responsible for protecting data. Sources: The approach is informed by known patterns in microservice authorization (e.g., distributed policy enforcement
alexanderlolis.com
, caching strategies
redis.io
) and by lessons from community discussions on ABAC in microservices (like avoiding per-object central checks for list endpoints
stackoverflow.com
). We also took inspiration from industry solutions (Google’s Zanzibar as a centralized model, Oso and others for policy-as-code) to ensure our design remains robust but simpler to implement within a Django context. The balance struck here is meant to give the consistency of a central system with the performance of localized checks – a strategy noted as a valid solution by practitioners
alexanderlolis.com
osohq.com
, and tailored to our Python/Django environment.
