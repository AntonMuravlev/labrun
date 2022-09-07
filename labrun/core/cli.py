import click

from labrun.core.control import Control


@click.command()
@click.option("--labdata", "-l")
@click.option("--nobootstrap", is_flag=True)
def cli(labdata, nobootstrap):
    control = Control(labdata)
    if nobootstrap:
        control.push_config_to_nodes(nobootstrap=True)
        control.config_post_check()
    else:
        control.bootstrap_nodes()
        control.push_config_to_nodes()
        control.config_post_check()


if __name__ == "__main__":
    cli()
