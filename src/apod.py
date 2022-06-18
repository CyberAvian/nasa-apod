"""
Fetches APOD images within a specified date range and saves them to disk.
"""

import json
import os

import requests


class Apod:
    def __init__(self, images_dir: str = None) -> None:
        """
        Create the necessary directories and files to store image data and images.
        resource_dir is a directory called Resources that will contain an images directory, an api key file, and a responses.json file
        """
        
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        if not images_dir:
            images_dir = os.path.join(self.data_dir, "images")
        self.images_dir = images_dir
        
        self.images_path_file = os.path.join(self.data_dir, "images_path.txt")
        self.api_key_file = os.path.join(self.data_dir, "api_key.txt")
        self.responses_file = os.path.join(self.data_dir, "responses.json")

    # Main Function that runs through the entire process of requesting and saving APOD images
    def main(self, date: str = None, start_date: str = None, end_date: str = None, count: int = None):
        """
        Automates the process of fetching a response, parsing the images, and saving the images.
        """

        # Handle Response
        try:
            response = self.get_response(date, start_date, end_date, count)
        except ValueError as errv:
            print(errv)
            print("Exiting")
            return 0
        formatted_response = self.format_response(response)
        self.save_response(formatted_response)

        # Handle Images
        image_urls = self.get_image_urls(formatted_response)
        images = self.get_images(image_urls)
        if images:
            self.save_images(images)
        else:
            print("Nothing to save")

        print("Finished running")

        input("Press enter to quit")

    # Get Web Request for Specified Dates
    def get_response(self, date: str = None, start_date: str = None, end_date: str = None, count: int = None) -> requests.models.Response:
        """
        Returns an HTTP response from the NASA APOD API.

        Optional Parameters:
            date        -   Gets the specified date. 
                            Must be used alone.
            start_date  -   The start of the desired date range. 
                            Can only be used with end_date.
            end_date    -   The end of the desired date range. start_date must be specified to use this.
                            If start_date is used without end_date, end_date will default to Today.
                            Can only be used with start_date.
            count       -   Specifies the number of randomly chosen images to retrieve.
                            Must be used alone.
        
        If no parameters are set, the API will default to pulling the APOD image for today.

        If more than one parameter was set, only the first in the order of [date, start_date, count] will be called.
            Examples:   If date and count are specified, only date will run.
                        If start_date and count are specified, only start_date will run.

        If end_date is set without start_date, it will be ignored. The response will be as though no parameters were set.

        If any errors are encountered fetching the response, an exception is raised in a ValueError exception
        """

        print("Creating request url")
        try:
            with open(self.api_key_file, "r", encoding="utf-8") as api_file:
                api_key = api_file.readlines()[0].rstrip()
            url = f'https://api.nasa.gov/planetary/apod?api_key={api_key}'
        except IndexError:
            raise ValueError(f"No API Key set.\nPlease set API Key in {self.api_key_file}")

        if date:
            url += f'&date={date}'
        elif start_date:
            url += f'&start_date={start_date}'
            # Since end_date is dependant on start_date and is optional, it is checked and set only when start_date is specified
            if end_date:
                url += f'&end_date={end_date}'
        elif count:
            url += f'&count={count}'

        try:
            print(f"Connecting to {url}")
            response = requests.get(url)
            response.raise_for_status()
            print("Successfully received response")
            return response
        except requests.exceptions.HTTPError as errh:
            raise ValueError(f"HTTP Error: {errh}.\nQuitting")
        except requests.exceptions.RequestException as err:
            raise ValueError(f"Ran into a problem fetching {url}.\nError: {err}.\nQuitting")

    # Turn Response Into List for Parsing
    def format_response(self, response: requests.models.Response) -> list[dict]:
        """
        Return the provided HTTP response as a list of dictionaries.

        The NASA APOD API returns a json string under response.text that contains the data for each photo.
        If multiple images were requested, this json string will be loaded as a list. 
        If a single image was requested, this json string will be loaded as a dictionary.
        To make everything consistent, this function will convert the response into a list if it isn't already.
        """

        query = json.loads(response.text)
        if isinstance(query, dict):
            # Just pop that query into a list and save back to the initial variable.
            query = [query]
        return query

    # Save Response for Future Reference
    def save_response(self, formatted_response: list[dict]) -> None:
        """
        Add the new HTTP response to the list of past responses, sort by date, filter out duplicates, and write the result to respones.json
        """

        past_responses = list()
        if os.path.getsize(self.responses_file) > 0:
            with open(self.responses_file, "r", encoding="utf-8") as response_file:        
                past_responses.extend(json.load(response_file))

        past_responses.extend(formatted_response)
        # Each image response has a key that specifies which date the image was featured on APOD
        # This is a convenient piece of data to sort the responses by
        past_responses.sort(key = lambda response: response["date"])

        # Remove any duplicate entries from the list
        filtered_past_responses = []
        [filtered_past_responses.append(response) for response in past_responses if response not in filtered_past_responses]

        print(f"Saving retrieved response to {self.responses_file}")
        # The entire response file was read in and stored in the self.past_responses variable, then filtered into filtered_past_responses
        # Writing to the file instead of appending to it will ensure no duplicates are added
        with open(self.responses_file, "w", encoding="utf-8") as response_file:
            json.dump(filtered_past_responses, response_file, ensure_ascii=False, indent=4)
        print("Save complete")

    # Get Image URLS from Response
    def get_image_urls(self, formatted_response: list[dict]) -> list[str]:
        """
        Return a list of image urls from a given HTTP response.

        Note that this response was formatted to be a list during the format_response stage.
        If running this as a standalone function, ensure formatted_response is a list.
        """

        print("Getting Image Urls from response")
        image_urls = list()
        for image_json in formatted_response:
            # Every image json block should have the hdurl key, but better safe than sorry
            if "hdurl" in image_json:
                image_url = image_json["hdurl"]
            else:
                image_url = image_json["url"]
            print(f"Found {image_url}")
            image_urls.append(image_url)
        
        return image_urls

    # Request Image URL
    def get_images(self, image_urls: list[str]) -> list[tuple]:
        """
        Return a list of tuples in the format of [(image_name, image_data)]
        This function first checks if the image has already been pulled and saved.
        The assumption is that the image name will be the .jpg name in the url.
        This is to reduce the total number of requests sent to the NASA APOD API.
        """
        
        print("Requesting images")
        images = list()
        for url in image_urls:
            image_name = os.path.split(url)[1]
            # If the image has already been saved, there is no need to request it again
            if os.path.exists(os.path.join(self.images_dir, image_name)):
                print(f"Skipping {image_name}. Already exists.")
                continue
            try:
                print(f"Requesting {url}")
                image_data = requests.get(url)
                image_data.raise_for_status()
                images.append((image_name, image_data))
            except requests.exceptions.HTTPError as errh:
                raise ValueError(f"HTTP Error: {errh}.\nQuitting")
            except requests.exceptions.RequestException as err:
                raise ValueError(f"Ran into a problem fetching {url}.\nError: {err}.\nQuitting")

        return images

    # Save Requested Images
    def save_images(self, images: list[tuple]) -> None:
        """
        Save images to the defined image directory. By default, this is apod/resources/images.
        Images should be a list of tuples in the form [(image_name, image_data)]
        """
        
        print(f"Saving images")
        for image in images:
            image_name = image[0]
            image_data = image[1]
            image_filename = os.path.join(self.images_dir, image_name)
            print(f"Saving {image_name} to {image_filename}")
            # image_data is binary data
            with open(image_filename, "wb") as image_file:
                image_file.write(image_data.content)
        print("Saving complete")
