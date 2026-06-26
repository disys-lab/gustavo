# Gustavo

Gustavo is a container orchestration framework constructed for Demo A3 under Research Thrust 2 of [NASA HOME STRI Project](https://homestri.ucdavis.edu/research). 
Gustavo is designed to be a one stop shop for administering applications in an **autonomous, self aware** fashion.
Gustavo is available as a **web-based GUI** (via Docker containers) or via **Command Line Interface** and can be run on Linux/Mac Environments as well as under Windows with the help of Windows Subsystem for Linux (WSL).

## Documentation

Gustavo's documentation is hosted at: **[https://disys-lab.github.io/gustavo/](https://disys-lab.github.io/gustavo/)**

For the CLI command reference and basic usage, see the [CLI Reference](https://disys-lab.github.io/gustavo/cli/index.md/) section of the documentation.

The recommended approach for most users is the Docker-based web interface, which provides a user-friendly dashboard and REST API. See the [Quickstart](https://disys-lab.github.io/gustavo/quickstart.md) for a 5-minute installation guide.

```
Usage: gustavo [OPTIONS] COMMAND [ARGS]...

  Manage gustavo from a simple CLI.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  apps          Manage applications
  cache         obtain status of various workers on the platform
  device-group  Manage device groups.
  manager       Administer the manager.
  ping          check nebula api responds
  prune         prune images.
  registry      Manage local registry.
  utils         utility commands
  worker        Manage worker.
```

## Common Gotchas

- **Podman**: You must login using ```podman login docker.io``` prior to launching this tool. Else there will be authentication errors.
- **Docker in bridge mode**: If managed services (Redis, MongoDB, etc.) run in Docker containers, use container names (via a shared network) rather than dynamic bridge IPs. Bridge IPs change when containers restart.

## Development and Maintenance

Gustavo was conceived and developed by researchers at Oklahoma State University and Georgia Tech.

- [Paritosh Ramanan](https://ceat.okstate.edu/iem/people/ramanan-faculty-profile.html) — Oklahoma State University
- [Nagi Gebraeel](https://www.isye.gatech.edu/users/nagi-gebraeel) — Georgia Tech

## Contributing

Contributions are welcome! Please see the [Contributing Guide](https://disys-lab.github.io/gustavo/contributing.md) for details.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
