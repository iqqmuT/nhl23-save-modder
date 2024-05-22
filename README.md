# NHL23 Save Modder

## Setup

Create Docker image:

```bash
$ docker build -t nhl23 .
```

## Usage

First you need to [extract](https://github.com/bucanero/apollo-ps4) these files from NHL23 save file:

* `INDEX`
* `DATA`

After you have them, you can use this tool to extract `database.db` from `DATA` by running:


```shell
$ ./extract.sh INDEX DATA database.db
```

Modify `database.db`. After that recreate `INDEX` and `DATA`:

```shell
$ ./pack.py INDEX DATA database.db
```

New subdirectory `build/` is created with rewritten `INDEX` and `DATA` files. Import them back to the NHL23 save file and be happy.

### DATA file

* DATA contains `CRCValue` but you do not have to modify it

## Docs

LZ4 format
https://github.com/lz4/lz4/blob/dev/doc/lz4_Frame_format.md
