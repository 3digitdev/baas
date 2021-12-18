# Boolean-as-a-Service

_A stupid project for managing flags_

## Installation

This project uses `poetry` for managing the environment and packages.  The project is built 
using Python 3.9, and thus will require it, but `poetry` will manage a virtual environment 
automatically for you.

[Install poetry](https://python-poetry.org/docs/master/), then just run `poetry install` 
from within the root of the project

Additionally, this uses `black` formatting as a pre-commit hook.  In order for this to run,
you'll need to install `pre-commit` locally using `python3 -m pip install pre-commit`,
then run `pre-commit install` at the root of the project to enable the `black` hook
_(make sure you're doing this in your base machine's Python interpreter!)_

## Running the app

For local dev convenience, a Docker Compose script has been setup that will run a MySQL DB with test data
alongside the Sanic API.  In order to start it up:

```shell
docker compose build
docker compose up
```

This will start the DB on `localhost:3306`, and the API will be on `localhost:8000`.

For hitting the API, we recommend using the [Insomnia Client](https://insomnia.rest/download).

## Endpoints

### User Management

- `POST /users`:  Create a new user.

This endpoint requires a body like `{"secret": "hunter2"}`.  
The secret will act as your password from now on.

You will be provided an auto-generated `key` in the response.  
**DO NOT LOSE THIS.**  This app doesn't have user recovery at all.

**Unused users will be deleted automatically after 30d of inactivity.**

### Bool Management

- All of these require you to provide authentication via the `Authentication: Basic` header.  
  - `username` is the `key` you were provided when you signed up
  - `password` is the `secret` you provided when you signed up
- All of these except `GET /bools` allows for a `simple` boolean query param.
  - if `true`, this will change the response body from `{"bool": {...}}` to a simple `{"value": false}` for easy parsing.
  - The default for this is `false`.

- `GET /bools`:  List all bools for your User
- `POST /bools`: Create a new bool for your User
  - Body:  `{"name": "Some_Bool_Name", "value": false}`
    - All fields are required. `value` must be a `boolean`
- `GET /bools/<id:int>`:  Get a single bool by ID for your User
- `POST /bools/<id:int>`:  Toggle the value of a bool for your User
- `DELETE /bools/<id:int>`:  Delete one of your bools.

#### Response Structure

**Default**
```json
{
  "bool": {
    "id": 2,
    "name": "SomeBool",
    "value": false,
    "owner": 1
  }
}
```
**Using `?simple=true`**
```json
{ "value": false }
```