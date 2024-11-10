import argparse
import json
import os
from datetime import datetime, timedelta

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
            "From Random Days": self.get_random_images,
            "Since Last Requested Day": self.get_from_last_image
        }

    def main(self):
        """
        Entry point into script.
        """

        print("Checking for existing images directory")
        try:
            images_dir = self.setup()
            apod = Apod(images_dir)
        except ValueError as errv:
            print(errv)
            return 0

        args = self.get_args()
        try:
            args.func(apod, cmd_args=args)
        except ValueError as errv: # There was an error running the selected function
            print(errv)
            print("Quitting")
        except AttributeError: # There were no arguments passed to the program
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
        """"
        Sets the error message. If message is not specified, it will set error to an empty string.
        """
        
        self.err = message

    def clear_screen(self):
        """
        Run clear console command based on detected OS
        """
        
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def get_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(help="Method of pulling images")
        
        single_day = subparsers.add_parser("single-day",
                                           aliases = ['sd'],
                                           help="pull images from a single day")
        single_day.add_argument("-d", "--date", default="", help="date to pull image from. YYYY-MM-DD format. defaults to today.")
        single_day.set_defaults(func=self.get_single_image)
        
        range_days = subparsers.add_parser("range-days",
                                           aliases = ['rgd'],
                                           help="pull images from a range of days")
        range_days.add_argument("start_date", help="first date in range. YYYY-MM-DD format")
        range_days.add_argument("-e", "--end-date", default="", help="last date in range. YYYY-MM-DD format. defaults to today.")
        range_days.set_defaults(func=self.get_range_images)

        random_days = subparsers.add_parser("random-days",
                                            aliases = ['rnd'],
                                            help="pulls provided number of random images")
        random_days.add_argument("count", help="number of images to pull")
        random_days.set_defaults(func=self.get_random_images)

        from_last_day = subparsers.add_parser("from-last-day",
                                              aliases = ['fld'],
                                              help="pulls images between today and the last requested image date")
        from_last_day.set_defaults(func=self.get_from_last_image)

        args = parser.parse_args()
        return args

    def setup(self):
        """
        Checks if the images directory has already been set up. If it hasn't, create it and then run the create for every other directory and file needed.
        """
        
        data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
        images_path_file = os.path.join(data_dir, "images_path.txt")

        # Once an images directory has been chosen, it should be saved in ./data/images_path.txt
        # If the data directory or images_path.txt file don't exist, or if the file is empty, an images directory is not set.
        if os.path.exists(data_dir) and os.path.exists(images_path_file) and os.path.getsize(images_path_file) > 0:
            images_dir = self.load_images_dir(images_path_file)
            print(f"Found {images_dir}")
        else:
            self.clear_screen()
            images_dir = self.get_images_dir(data_dir)
            api_key = self.get_api_key()
            self.clear_screen()
            print("\nSetting up file system")
            self.create_dirs(data_dir, images_dir, api_key)
            self.save_image_dir(images_path_file, images_dir)
            if api_key == "":
                raise ValueError(f"API Key not set.\nPlease add API Key to api_key.txt located in {images_dir}")

        return images_dir

    def get_images_dir(self, data_dir_path: str) -> str:
        """
        Get the path of the desired image directory from the user
        If no path is specified, will set it to the data directory
        """
        
        print("Provide a path to store the fetched images.")
        print("The path should be the absolute path to the folder the images are to be placed in.")
        images_dir = input("<Path> [./data/images]: ")
        if images_dir == "":
            images_dir = os.path.join(data_dir_path, "images")
        return images_dir

    def get_api_key(self) -> str:
        """
        Prompt the user for their api key to add to api_key.txt
        If the user prefers to do it manually, the key can be left blank
        User must fill in key before running program
        """
        
        print("\nEnter API Key.\nIf left blank, the program will exit after creating directories so you can add the key \
manually to the api_key.txt file.\nThis will be in the path you chose in the last step.")
        api_key = input("<Key>: ")
        return api_key

    def create_dirs(self, data_dir: str, images_dir: str, api_key: str) -> None:
        """
        Creates the required directories and files if not already present.
        """

        images_path_file = os.path.join(data_dir, "images_path.txt")
        api_key_file = os.path.join(data_dir, "api_key.txt")
        responses_file = os.path.join(data_dir, "responses.json")

        directories = [data_dir, images_dir, images_dir]
        files = [images_path_file, api_key_file, responses_file]

        for directory in directories:
            if not os.path.exists(directory):
                print(f"Creating {directory}")
                os.mkdir(directory)
            else:
                print(f"Skipping {directory}. Already exists.")

        for file in files:
            if not os.path.exists(file):
                print(f"Creating {file}")
                if file == api_key_file and api_key != "":
                    with open(file, "w", encoding="utf-8") as make_file:
                        make_file.write(api_key)
                else:
                    with open(file, "x", encoding="utf-8") as make_file:
                        pass
            else:
                print(f"Skipping {file}. Already exists.")

    # Save the path to the Apod Image Directory
    def save_image_dir(self, images_path_file: str, images_dir: str) -> None:
        """
        Saves the path to the image directory to the data/images_path.txt file
        """
        
        with open(images_path_file, "w", encoding="utf-8") as images_file:
            images_file.write(images_dir)

    # Load the path to the Apod Image Directory
    def load_images_dir(self, images_path_file: str) -> None:
        """
        Loads a saved image directory from data/images_path.txt
        """
        
        with open(images_path_file, "r", encoding="utf-8") as images_file:
            images_path = images_file.read()
        return images_path

    def get_option(self) -> str:
        """
        Prompt for how images should be pulled.
        """

        print("\nNasa APOD Image Saver\n")
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

    def get_single_image(self, apod_handler: Apod, image_date: str = None, cmd_args: argparse.Namespace = None) -> None:
        """
        Pull a single image from a specified date

        cmd_args are command line arguments. They get checked first
        image_date is the date to pull images from. Can't run with cmd_args
        """
        
        if cmd_args:
            image_date = cmd_args.date
        elif not image_date:
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

    def get_range_images(self, apod_handler: Apod, image_start_date: str = None, image_end_date: str = None, cmd_args: argparse.Namespace = None) -> None:
        """
        Pull images from a specified date range
        Date range is defined by a start date and an end date
        If no end date is provided, it will be set to today
        """
        
        if cmd_args:
            print(cmd_args)
            image_start_date = cmd_args.start_date
            image_end_date = cmd_args.end_date
        elif not image_start_date or not image_end_date:
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

    def get_random_images(self, apod_handler: Apod, image_count: int = None, cmd_args: argparse.Namespace = None) -> None:
        """
        Pull a specified random number of images from random days
        """
        
        if cmd_args:
            image_count = cmd_args.count
        elif not image_count:
            self.clear_screen()
            print("Pull Images From Random Days\n")
            print("Enter the number of images to pull. Must be an integer.")
            image_count = input("<Number>: ")
            if not image_count.isdigit():
                raise ValueError("Input must be an integer.")
        self.clear_screen()
        apod_handler.main(count=image_count)

    def get_from_last_image(self, apod_handler: Apod, cmd_args: argparse.Namespace = None):
        """
        Fetches images starting from the date of the last image fetched and ending today.
        Checks responses.json to see what the most recent image date is.
        """

        try:
            with open(apod_handler.responses_file, "r", encoding="utf-8") as r_file:
                images = json.load(r_file)
            last_image_date = images[-1]["date"]
            if last_image_date != datetime.strftime(datetime.today(), "%Y-%m-%d"):
                start_date = datetime.strftime(datetime.strptime(last_image_date, "%Y-%m-%d") + timedelta(days=1), "%Y-%m-%d")
                self.clear_screen()
                apod_handler.main(start_date=start_date)
            else:
                print("Nothing to pull. All images already pulled.")
        except json.JSONDecodeError:
            raise ValueError("No previous requests.\nRun another option.")

if __name__=='__main__':
    program = Main()
    program.main()
