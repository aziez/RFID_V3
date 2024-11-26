import os
import sys
import argparse
import subprocess


class PyInstallerBuilder:
    def __init__(self):
        self.base_options = [
            '--windowed',  # No console window
            '--noconfirm',  # Overwrite output directory
        ]

        self.hidden_imports = [
            'windows_curses',
            'pkg_resources',
        ]

        self.additional_options = []
        self.icon_path = None

    def add_hidden_import(self, module):
        """Add additional hidden imports."""
        self.hidden_imports.append(module)
        return self

    def set_icon(self, icon_path):
        """Set application icon."""
        if os.path.exists(icon_path):
            self.icon_path = icon_path
        else:
            print(f"Warning: Icon path {icon_path} does not exist.")
        return self

    def add_data_files(self, data_files):
        """Add additional data files."""
        for data in data_files:
            self.additional_options.extend(['--add-data', data])
        return self

    def build(self, input_file, output_name=None):
        """
        Build the executable

        :param input_file: Main Python script to build
        :param output_name: Name of the output executable (optional)
        """
        # Prepare command
        cmd = ['pyinstaller', '-F', input_file]

        # Add base options
        cmd.extend(self.base_options)

        # Add hidden imports
        for module in self.hidden_imports:
            cmd.extend(['--hidden-import', module])

        # Add icon if specified
        if self.icon_path:
            cmd.extend(['--icon', self.icon_path])

        # Add additional options
        cmd.extend(self.additional_options)

        # Set output name if provided
        if output_name:
            cmd.extend(['--name', output_name])

        try:
            # Run PyInstaller
            print("Building executable with command:")
            print(" ".join(cmd))

            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            # Print standard output and error
            print("Build Output:")
            print(result.stdout)

            print("\nBuild Complete!")
            return True

        except subprocess.CalledProcessError as e:
            print("Build Failed:")
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
            return False


def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Flexible PyInstaller Build Script')
    parser.add_argument('input_file', help='Main Python script to build')
    parser.add_argument('--name', help='Output executable name', default=None)
    parser.add_argument('--icon', help='Path to icon file', default=None)
    parser.add_argument('--extra-imports', nargs='*', help='Additional hidden imports', default=[])
    parser.add_argument('--data-files', nargs='*', help='Additional data files', default=[])

    # Parse arguments
    args = parser.parse_args()

    # Create builder
    builder = PyInstallerBuilder()

    # Add hidden imports
    for module in args.extra_imports:
        builder.add_hidden_import(module)

    # Set icon if provided
    if args.icon:
        builder.set_icon(args.icon)

    # Add data files
    if args.data_files:
        builder.add_data_files(args.data_files)

    # Build the executable
    builder.build(args.input_file, args.name)


if __name__ == '__main__':
    main()