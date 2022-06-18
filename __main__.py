import os
from datetime import datetime

try:
    from .src.apod import Apod
except ImportError:
    from src.apod import Apod


class Main:
    def __init__(self):
        self.err = ""
        self.options: dict = {
            "From a Single Day": self.get_single_image, 
            "From a Range of Days": self.get_range_images, 
            "From Random Days": self.get_random_images
        }

    def main(self):
        self.clear_screen()
        print("Checking for existing resource directory")
        try:
            resource_dir = self.setup()
            apod = Apod(resource_dir)
            input("Press enter to continue...")
        except ValueError as errv:
            print(errv)
            return 0

        while True:
            option = self.get_option()
            if option:
                self.set_err()
                break
            self.set_err("Invalid Option Number")
        
        # Lookup the selected option name in the options dictionary and call the associated method value
        while True:
            try:
                self.options[option](apod)
                break
            except ValueError as errv:
                self.err = errv

    def set_err(self, message: str = ""):
        self.err = message

    def clear_screen(self):
        # Run console clear command based on detected OS
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def setup(self):
        data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
        resource_dir_file = os.path.join(data_dir, "resource_dir_path.txt")

        # Once a resource directory has been chosen, it should be saved in ./data/resource_dir_path.txt
        # If the data directory or resource_dir_path.txt file don't exist, or if the file is empty, a resource directory is not set.
        if os.path.exists(data_dir) and os.path.exists(resource_dir_file) and os.path.getsize(resource_dir_file) > 0:
            resource_dir = self.load_resource_dir(resource_dir_file)
            print(f"Found {resource_dir}")
        else:
            self.clear_screen()
            resource_dir = self.get_resource_dir(data_dir)
            api_key = self.get_api_key()
            self.clear_screen()
            print("\nSetting up file system")
            self.create_resources(data_dir, resource_dir, api_key)
            self.save_resource_dir(resource_dir_file, resource_dir)
            if api_key == "":
                raise ValueError(f"API Key not set.\nPlease add API Key to api_key.txt located in {resource_dir}")

        return resource_dir

    def get_resource_dir(self, data_dir_path: str) -> str:
        print("Provide a path to store files used by this program.")
        print("This path will store images, the api key, and the responses from queries.\n")
        resource_dir = input("<Path> [./data/]: ")
        if resource_dir == "":
            resource_dir = os.path.join(data_dir_path, "resources")
        return resource_dir

    def get_api_key(self) -> str:
        print("\nEnter API Key.\nIf left blank, the program will exit after creating directories so you can add the key \
manually to the api_key.txt file.\nThis will be in the path you chose in the last step.")
        api_key = input("<Key>: ")
        return api_key

    def create_resources(self, data_dir: str, resource_dir: str, api_key: str) -> None:
        """
        Creates the required directories and files if not already present.
        """

        images_dir = os.path.join(resource_dir, "images")
        resource_dir_file = os.path.join(data_dir, "resource_dir_path.txt")
        api_key_file = os.path.join(data_dir, "api_key.txt")
        responses_file = os.path.join(resource_dir, "responses.json")

        directories = [data_dir, resource_dir, images_dir]
        files = [resource_dir_file, api_key_file, responses_file]

        for directory in directories:
            if not os.path.exists(directory):
                print(f"Creating {directory}")
                os.mkdir(directory)
            else:
                print(f"{directory} found. Skipping")

        for file in files:
            print(f"Checking if {file} exists")
            if not os.path.exists(file):
                print(f"Creating {file}")
                if file == api_key_file and api_key != "":
                    with open(file, "w", encoding="utf-8") as make_file:
                        make_file.write(api_key)
                else:
                    with open(file, "x", encoding="utf-8") as make_file:
                        pass
            else:
                print(f"{file} found. Skipping")

    # Save the path to the Apod Resource Directory
    def save_resource_dir(self, resource_dir_file: str, resource_dir: str) -> None:
        """
        Saves the path to the resource directory to data/resource_dir_path.txt
        """
        
        with open(resource_dir_file, "w", encoding="utf-8") as resource_file:
            resource_file.write(resource_dir)

    # Load the path to the Apod Resource Directory
    def load_resource_dir(self, resource_dir_file: str) -> None:
        """
        Loads a saved resource directory from data/resource_dir_path.txt
        """
        
        with open(resource_dir_file, "r", encoding="utf-8") as resource_file:
            resource_dir_path = resource_file.read()
        return resource_dir_path

    def get_option(self) -> str:
        self.clear_screen()
        print("Nasa APOD Image Saver\n")
        option_names = list(self.options.keys())
        print("How should images be pulled?\n")
        for i, option in enumerate(option_names, start=1):
            print(f"{i}. {option}")
        print(self.err)
        option_num = input("<Option>: ")

        # Ensure given option is an integer and exists
        if not option_num.isdigit() or int(option_num) not in range(1, len(option_names) + 1):
            return 0

        # Options are numbered starting at 1. Needs to be adjusted to match the 0 indexed list.
        selected_option = option_names[int(option_num) - 1]
        return selected_option

    def get_single_image(self, apod_handler: Apod, image_date: str = None) -> None:
        if not image_date:
            self.clear_screen()
            print("Pull Image From a Single Day\n")
            print("Enter the date to pull the image from. Use the format YYYY-MM-DD. Include dashes.")
            print(self.err)
            image_date = input("<Date> [Today]: ")

        self.clear_screen()
        if image_date != "":
            try:
                # This is just a test to verify the date is in the correct format
                datetime.strptime(image_date, "%Y-%m-%d")
                apod_handler.main(date=image_date)
            except ValueError:
                raise ValueError("Date must be in the format of YYYY-MM-DD")
        else:
            apod_handler.main()

    def get_range_images(self, apod_handler: Apod, image_start_date: str = None, image_end_date: str = None) -> None:
        if not image_start_date or not image_end_date:
            self.clear_screen()
            print("Pull Images From a Range of Days\n")
            print("Enter the start and end dates for the range to pull from. Use the format YYYY-MM-DD. Include dashes.")
            print(self.err)
        if not image_start_date:
            image_start_date = input("<Start Date>: ")
        if not image_end_date:
            image_end_date = input("<End Date> [Today]: ")

        try:
            datetime.strptime(image_start_date, "%Y-%m-%d")
            self.clear_screen()
            if image_end_date != "":
                datetime.strptime(image_end_date, "%Y-%m-%d")
                apod_handler.main(start_date=image_start_date, end_date=image_end_date)
            else:
                apod_handler.main(start_date=image_start_date)
        except ValueError:
            raise ValueError("Date must be in the format of YYYY-MM-DD")

    def get_random_images(self, apod_handler: Apod, image_count: int = None) -> None:
        if not image_count:
            self.clear_screen()
            print("Pull Images From Random Days\n")
            print("Enter the number of images to pull. Must be an integer.")
            image_count = input("<Number>: ")
            if not image_count.isdigit():
                raise ValueError("Input must be an integer.")
        self.clear_screen()
        apod_handler.main(count=image_count)

if __name__=='__main__':
    program = Main()
    program.main()
