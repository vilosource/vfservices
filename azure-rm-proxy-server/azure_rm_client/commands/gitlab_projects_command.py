import argparse
import logging
from typing import Dict, Any
from azure_rm_client.commands.base_command import BaseCommand
from azure_rm_client.commands import CommandRegistry
from azure_rm_client.formatters import get_formatter
from azure_rm_client.workers.gitlab_worker import GitLabWorker

logger = logging.getLogger(__name__)


@CommandRegistry.register
class GitLabProjectsCommand(BaseCommand):
    """
    Command for listing GitLab projects in a group.
    """

    def __init__(self, output_format: str = "table", base_url: str = "http://localhost:8000", args: argparse.Namespace = None):
        self.output_format = output_format
        self.base_url = base_url
        self.args = args  # Store the parsed arguments

    @property
    def name(self) -> str:
        return "gitlab-projects"

    @property
    def description(self) -> str:
        return "List all GitLab projects in a group."

    @classmethod
    def configure_parser(cls, subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "--format",
            default="table",
            choices=["table", "json", "yaml"],
            help="Output format (default: table)",
        )
        subparser.add_argument(
            "--group",
            required=True,
            help="GitLab group name or ID",
        )
        subparser.add_argument(
            "--all",
            action="store_true",
            help="Include all projects, including archived ones",
        )
        subparser.add_argument(
            "--refresh-cache",
            action="store_true",
            help="Bypass cache and fetch fresh data (default: False)",
        )

    @classmethod
    def get_param_mapping(cls) -> Dict[str, str]:
        return {"format": "output_format", "base_url": "base_url"}

    def execute(self) -> bool:
        logger.debug("Executing GitLabProjectsCommand with output_format=%s, base_url=%s", 
                    self.output_format, self.base_url)

        # Extract parameters from args
        group_name = self.args.group if hasattr(self.args, 'group') else None
        include_all = self.args.all if hasattr(self.args, 'all') else False
        refresh_cache = self.args.refresh_cache if hasattr(self.args, 'refresh_cache') else False

        if not group_name:
            logger.error("Group name or ID is required")
            return False

        # Use the GitLabWorker to fetch projects with proper base_url
        worker = GitLabWorker(base_url=self.base_url)
        
        try:
            projects = worker.list_projects(group_name, include_all=include_all, refresh_cache=refresh_cache)
            logger.debug("Fetched %d projects from group %s", len(projects), group_name)
        except Exception as e:
            logger.error("Failed to fetch GitLab projects: %s", e)
            return False

        # Format and print the projects
        formatter = get_formatter(self.output_format)
        logger.debug("Using formatter: %s", self.output_format)

        print(formatter.format(projects))
        logger.debug("GitLabProjectsCommand executed successfully")
        return True
