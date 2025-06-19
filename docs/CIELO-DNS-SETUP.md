# Cielo DNS Configuration

To test the multi-domain setup, the following DNS entries need to be configured:

## Domain: cielo.viloforge.com

Add these entries to your DNS or /etc/hosts file:

```
127.0.0.1 cielo.viloforge.com
127.0.0.1 www.cielo.viloforge.com
127.0.0.1 identity.cielo.viloforge.com
127.0.0.1 billing.cielo.viloforge.com
127.0.0.1 inventory.cielo.viloforge.com
```

## Testing

Once DNS is configured, you can test the multi-domain access:

1. Identity Provider from both domains:
   - https://identity.vfservices.viloforge.com/api/status/
   - https://identity.cielo.viloforge.com/api/status/

2. Main websites:
   - https://www.vfservices.viloforge.com/ (VF Services website)
   - https://www.cielo.viloforge.com/ (Cielo website)

## Production Setup

For production, configure proper DNS A records pointing to your server's IP address for all the subdomains listed above.