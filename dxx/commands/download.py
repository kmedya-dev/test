import click
from .. import config as config_module
from ..downloader import download_from_url
from ..logger import logger

@click.command()
@click.argument('package_or_url')
def download(package_or_url):
    """
    Downloads a package by name (from configuration) or from a direct URL.
    """
    if package_or_url.startswith(('http://', 'https://')):
        url = package_or_url
        logger.info(f"Downloading from direct URL: {url}")
        download_from_url(url)
    else:
        package_name = package_or_url
        logger.info(f"Attempting to download package by name: {package_name}")
        
        config = config_module.load_config()
        
        if config and 'package_name' in config and package_name in config.get('package_name', {}):
            url = config['package_name'][package_name]
            logger.info(f"Found URL for '{package_name}': {url}")
            download_from_url(url, package_name=package_name)
        else:
            message = f"Package '{package_name}' not found in the configuration."
            logger.error(message)
            click.echo(message)
            if config and 'package_name' in config:
                available_packages = list(config.get('package_name', {}).keys())
                if available_packages:
                    click.echo(f"Available packages are: {', '.join(available_packages)}")
