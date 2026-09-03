# Gustavo

Gustavo is a container orchestration framework constructed for Demo A3 under Research Thrust 2 of [NASA HOME STRI Project](https://homestri.ucdavis.edu/research). 
Gustavo is designed to be a one stop shop for administering applications in an **autonomous, self aware** fashion.
Gustavo is available as a **web-based GUI** (via Docker containers) or via **Command Line Interface** and can be run on Linux/Mac Environments as well as under Windows with the help of Windows Subsystem for Linux (WSL).

## Try it now

Two commands, no setup, no existing Nebula platform required:

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/disys-lab/gustavo/main/sample_config_files/docker-compose.quickstart.yml
docker compose up -d
```

Open [http://localhost:3000](http://localhost:3000). See the [Quickstart](https://disys-lab.github.io/gustavo/quickstart.md) for connecting this to a real Nebula platform.

## Documentation

Full documentation is available at: **[https://disys-lab.github.io/gustavo/](https://disys-lab.github.io/gustavo/)**

For a 5-minute installation guide, see the [Quickstart](https://disys-lab.github.io/gustavo/quickstart.md).

For the CLI command reference and basic usage, see the [CLI Reference](https://disys-lab.github.io/gustavo/cli/index.md) in the documentation.

For troubleshooting, see the [documentation](https://disys-lab.github.io/gustavo/).

## Development

Gustavo was conceived and developed by researchers at Oklahoma State University and Georgia Tech.

- [Paritosh Ramanan](https://ceat.okstate.edu/iem/people/ramanan-faculty-profile.html) — Oklahoma State University
- [Nagi Gebraeel](https://www.isye.gatech.edu/users/nagi-gebraeel) — Georgia Tech

See the [Developer Guide](https://disys-lab.github.io/gustavo/contributing.md) for setup and contribution details.

## Contributing

Contributions are welcome! Please see the [Contributing Guide](https://disys-lab.github.io/gustavo/contributing.md) for details.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
