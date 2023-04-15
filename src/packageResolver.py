import os
from dataclasses import dataclass
import pprint
import click


@dataclass
class PackageVersion:
    name: str
    version: int

    def __hash__(self) -> int:
        return hash((self.name, self.version))

    def __repl__(self) -> str:
        return f"""[*] {self.name} {self.version}"""

    def __str__(self) -> str:
        return f"""[*] {self.name} {self.version}"""

@dataclass
class DependencyPackages:
    dependency_packages: dict[PackageVersion, list[PackageVersion]]

    def __repr__(self) -> str:
        return pprint.pformat(self.dependency_packages)

    def __str__(self) -> str:
        return pprint.pformat(self.dependency_packages)

# PackageResolver
class PackageResolver:

    def __init__(self, path_to_file='data/packageIndex.txt', is_relative=True):

        self.dependency_packages, ok = self.parse_data_from_txt(path_to_file, is_relative)
        
        if not ok:
            raise "File is not exists"

    def parse_data_from_txt(self, path_to_file, is_relative=True):
        if is_relative:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            path_to_file = os.path.join(dir_path, path_to_file)

        with open(path_to_file, 'r', encoding='utf-8') as file:
            data = file.read()
            
            # DependencyPackages|dependency_packagesdict[PackageVersion, list[PackageVersion]]
            package_dep_dict = dict()

            for line in data.split("\n"):
                    key_value = line.split(':')
                    assert (len(key_value) == 2)

                    key_name = key_value[0].split(' ')[0]
                    key_version_package = int(key_value[0].split(' ')[1].strip())

                    package_key = PackageVersion(key_name, key_version_package)

                    
                    for dep_package in key_value[1].split(','):
                        name_and_version = dep_package.strip().split(' ')
                        if not (len(name_and_version) == 2):
                            package_dep_dict[package_key] = []
                            break

                        key_name_dep, key_version_package_dep = name_and_version
                        
                         
                        

                        key_version_package_dep = key_version_package_dep.split('..')
                        assert(len(key_version_package_dep) <= 2)
                        if len(key_version_package_dep) == 1:
                            range_version = range(int(key_version_package_dep[0]), int(key_version_package_dep[0]) + 1)
                        else:
                            range_version = range(int(key_version_package_dep[0]), int(key_version_package_dep[1]) + 1)
                        
                        for version_dep_package in range_version:
                            package_value = PackageVersion(key_name_dep, version_dep_package)
                            
                            if package_key not in package_dep_dict:
                                package_dep_dict[package_key] = []

                            package_dep_dict[package_key].append(package_value)
                            


            return DependencyPackages(package_dep_dict), True
        
        return None, False


    def latest_version(self, name):
        latest_version = None

        for package_version in self.dependency_packages.dependency_packages:
            if package_version.name == name:
                if latest_version is None:
                    latest_version = package_version.version
                else:
                    latest_version = max(package_version.version, latest_version)

        return latest_version

    def transitive_dependencies(self, package_version: PackageVersion):
        stack_packages = []
        visited = dict()
        terminal = dict()

        is_circle = False
        def dfs(package_version: PackageVersion):
            nonlocal is_circle
            if is_circle:
                return

            visited[package_version.name] = True
            stack_packages.append(package_version)
            

            for cur_package_version in self.dependency_packages.dependency_packages[package_version]:

                if (cur_package_version.name not in visited) or \
                    (not visited[cur_package_version.name]):
                    dfs(cur_package_version)
                    continue

                if  cur_package_version.name not in terminal:
                    is_circle = True
                    stack_packages.append(cur_package_version)
                    return
            
            terminal[package_version.name] = True
            # visited[package_version.name] = False
            # stack_packages.pop()
        
        dfs(package_version)

        return stack_packages, is_circle


# cli 
@click.command()
@click.option('--latest_version', '-lv', is_flag=True, help='Show the latest version for a given package name')
@click.option('--transitive_dependencies', '-td', is_flag=True, help='For a given package version print a possible set of all transitive dependencies with their versions or a useful message about version conflict.')
@click.argument('name')
@click.option('--version', '-v', default=None, help="Specify version of package")
def cli(latest_version, transitive_dependencies, name, version):
    """
        name: str | name of package
    """
    package_resolver = PackageResolver()
    # dependency_packages, ok = package_resolver.parse_data_from_txt(path_to_file='data/packageIndex.txt')

    if latest_version:
        res_latest_version = package_resolver.latest_version(name)
        if res_latest_version is None:
            click.echo(f"This is package not found.")
        else:
            click.echo(f"Package {name} has latest version {res_latest_version}.")

    if transitive_dependencies:
        assert version is not None
        version = int(version)

        package_version = PackageVersion(name, version)
        stack_packages, is_circle = package_resolver.transitive_dependencies(package_version)
        if is_circle:
            click.echo("Сyclic dependency of packages!")
            click.echo("The correspond dependency have conflict:")
            for cur_package_version in stack_packages:
                click.echo(f"{cur_package_version}")
        else:
            click.echo("Package dependency resolved.")
            click.echo("The correspond packages need to install:")
            for cur_package_version in stack_packages:
                click.echo(f"{cur_package_version}")

if __name__ == "__main__":
    
    cli()
    
# python3 packageResolver.py -td --version=0  digs ok
# python3 packageResolver.py -td --version=0  unbemourned ok
# python3 packageResolver.py -td --version=2  pidgizing notok
# 




