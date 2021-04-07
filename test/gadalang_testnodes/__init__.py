"""Collection of nodes used in unittests.

PYTHONPATH will be automatically set so Python can find this package.
"""
import sys
import json
import asyncio
import pygada_runtime


async def run():
    data = await pygada_runtime.read_json(sys.stdin)

    input = data.get("input", None)
    if input:
        with open(input, "r") as f:
            content = json.loads(f.read())
    else:
        content = data.get("data", {})

    output = data.get("output", None)
    if output:
        with open(output, "w") as f:
            f.write(json.dumps(content))

    pygada_runtime.write_json(sys.stdout, {"data": content})


def main(argv):
    """Entrypoint used with **python** runner."""
    # parser = pygada_runtime.get_parser("json")
    # pygada_runtime.main(run, parser, argv)

    asyncio.run(run())


if __name__ == "__main__":
    main(sys.argv)
