import click

from labrun.core.control import Control


@click.command()
@click.option("--labdata", "-l")
def cli(labdata):
    control = Control(labdata)
    control.labparams.loopback_prefix.allocate_next_free_ip()#must be fixed
    control.bootstrap_nodes()
    control.push_config_to_nodes()


if __name__ == "__main__":
    cli()