# APOD

APOD pulls Nasa Astronomy Photos of the Day and stores both the request json and images.

## Installation

Pull from github then install requirements from requirements.txt

```shell
git pull https://github.com/CyberAvian/nasa-apod.git

cd nasa-apod

pip install -r requirements.txt
```

## Usage

There are several ways to use this script.

1. Call from the command line
    - This is an interactive script that sets up the folder and file structure and then allows various methods of pulling images.

    ```Shell
    python -m nasa-apod
    ```
2. Create an object using the Apod class found in src/apod.py
    - The initializer is expecting the path of the images directory. The class will not create this if it doesn't exist.
    - The object also assumes there is a directory called data in the nasa-apod folder that contains an api_key.txt file, an images_path.txt file, and a responses.json file. The class will not create these if they don't exist.
        - api_key.txt stores your nasa apod key
        - images_path.txt stores the path to the images directory
        - responses.json stores the requests that get pulled when running the script

## License
[MIT](https://choosealicense.com/licenses/mit/)