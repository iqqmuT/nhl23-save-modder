# NHL23 Save Modder

## Setup

Create Docker image:

```bash
$ docker build -t nhl23 .
```

## Usage

First you need to extract these files from NHL23 save file:

* `INDEX`
* `DATA`

After you have them, you can use this tool to extract `database.db` from `DATA` by running:


```shell
$ docker run --rm -it -v $PWD:/code nhl23 python3 extract.py INDEX DATA database.db
```

Modify `database.db`. After that recreate `INDEX` and `DATA`:

```shell
$ docker run --rm -it -v $PWD:/code nhl23 python3 pack.py INDEX DATA database.db
```

New subdirectory `build/` is created with rewritten `INDEX` and `DATA` files. Import them back to the NHL23 save file and be happy.

### DATA file

* DATA contains `CRCValue` but you do not have to modify it
