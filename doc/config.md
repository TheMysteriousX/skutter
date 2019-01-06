# Configuration

## Environment

`SKUTTER`

If present, the service will run interactively and emit debug messages.

## Service

`systemd` _(boolean)_

Whether this service is to run under systemd - if set to false, the service will attempt to daemonise itself.

`rundir` _(string)_

Location of the runtime directory on the host system.

`v6-only` _(boolean)_

Determines if the service will run with both IPv4 and IPv6 enabled, or IPv6 only. Please note that running with IPv6 is not supported by the most mainstream OS vendors, so will not be supported by Skutter.

`self-uuid` _(str)_

This is a unique identifier that is used by Skutter to track its own actions (e.g. firewall rules) when interacting with an external process that does not persist sufficient state for Skutter's actions to be idempotent.

It's not recommended to change this value - it is not used in a security sensitive context, but shouldn't break anything as long as Skutter exits cleanly before the UUID is changed.

## Jobs

### Check

`check` _(string)_

The name of the check plugin to use.

`config` _(dictionary)_

This block will be passed to the check plugin; its format is specific to the plugin.

### positive-action

`module` _(string)_

The name of the action plugin to use if the check succeeds.

`config` _(dictionary)_

This block will be passed to the action plugin; its format is specific to the plugin.

### negative-action

`module` _(string)_

The name of the action plugin to use if the check fails.

`config` _(dictionary)_

This block will be passed to the action plugin; its format is specific to the plugin.
