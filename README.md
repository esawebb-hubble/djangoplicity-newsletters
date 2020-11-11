# Djangoplicity Newsletters

![Coverage](https://img.shields.io/codecov/c/github/djangoplicity/djangoplicity-newsletters/develop)
![Size](https://img.shields.io/github/repo-size/djangoplicity/djangoplicity-newsletters)
![License](https://img.shields.io/github/license/djangoplicity/djangoplicity-newsletters)
![Language](https://img.shields.io/github/languages/top/djangoplicity/djangoplicity-newsletters)

Djangoplicity Newsletters is a dependency of the [Djangoplicity](https://github.com/djangoplicity/djangoplicity) CMS
created by the European Southern Observatory (ESO) for managing Newsletters, Mailing Lists, Subscribers and so much more.

* [Requirements](#requirements)
* [Installation](#installation)
    * [Requirements](#requirements)
    * [Migrations](#migrations)
* [Development](#development)
* [License](#license)

## Installation

If you are using Docker, you can look for an example in [Dockerfile](Dockerfile) and [docker-compose.yml](docker-compose.yml) files located in the root
of the repository.

### Requirements

Djangoplicity Newsletters currently supports Python 2.7 and Python 3+.

You must install Djangoplicity Newsletters using the Github repository, so add the following packages to your
requirements depending on the Python version you are using.
```
# Asynchronous Task Queue
celery==4.3.0

# For Python 3+

# Djangoplicity actions
git+https://@github.com/djangoplicity/djangoplicity-actions@release/python3

# Djangoplicity newsletters
git+https://@github.com/djangoplicity/djangoplicity-newsletters.git@release/python3

# Djangoplicity
git+https://@github.com/djangoplicity/djangoplicity.git@release/python3

# For Python 2.7

# Djangoplicity actions
git+https://@github.com/djangoplicity/djangoplicity-actions@develop

# Djangoplicity newsletters
git+https://@github.com/djangoplicity/djangoplicity-newsletters.git@develop

# Djangoplicity
git+https://@github.com/djangoplicity/djangoplicity.git@develop
```
Celery is also required for some asynchronous tasks to work.

Now include the package in your [INSTALLED_APPS](https://github.com/djangoplicity/djangoplicity-newsletters/blob/develop/test_project/settings.py#L83)

Djangoplicity requires some additional settings in order to work, so add this configuration to your [settings.py](https://github.com/djangoplicity/djangoplicity-newsletters/blob/develop/test_project/settings.py#L199)
file (you don't have to include those files in your assets)

You also have to add [tinymce](https://github.com/djangoplicity/djangoplicity-newsletters/blob/develop/test_project/settings.py#L219) settings

Now, add the following imports to your [CELERY_IMPORTS](https://github.com/djangoplicity/djangoplicity-newsletters/blob/develop/test_project/settings.py#L249) variable. You can create it if you don't have one, just be sure that you have properly configured Celery for the project.

Next, you have to register the models in your [admin.py](https://github.com/djangoplicity/djangoplicity-newsletters/blob/develop/test_project/admin.py) file.

### Migrations

Next, make the migrations for the `django_mailman` package:
```bash
python manage.py makemigrations django_mailman
```
And run the migrations:
```bash
python manage.py migrate
```

## Development

This repository includes an example project for local development located in the [test_project](test_project) folder. You can find
there the basic configuration to get a project working.
 
### Cloning the repository

In your terminal run the command:

```` 
git clone https://gitlab.com/djangoplicity/djangoplicity-newsletters.git
````

## Mailchimp API Key Configuration

In the folder test_project you have a file named .env.example, this file serve to declare the environment variables API Key and List ID of Mailchimp.
Remove the extension .example of this file and configure your `NEWSLETTERS_MAILCHIMP_API_KEY` and `NEWSLETTERS_MAILCHIMP_LIST_ID` variables of Mailchimp.

### Running the project

All the configuration to start the project is present in the docker-compose.yml, Dockerfile and .env previously configured,
then at this point a single command is required to download all the dependencies and run the project:

```` 
docker-compose --env-file ./test_project/.env up
````

> The previous command reads the config from docker-compose.yml and .env file. 

When the process finishes, the server will be available at *`localhost:8002`*

To stop containers press `CTRL + C` in Windows or `⌘ + C` in MacOS

If the dependencies change, you should recreate the docker images and start the containers again with this command:

```` 
docker-compose --env-file ./test_project/.env up --build
````

### Additional commands

Inside the `Makefile` there are multiple command shortcuts, they can be run in UNIX systems like this:

```
make <command-name>
```

E.g.

```
make migrate
```

> In Windows you can just copy and paste the related command

## License

This repository is released under the [GPL-2.0 License](LICENSE)
