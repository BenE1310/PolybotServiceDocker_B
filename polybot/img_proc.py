from pathlib import Path
from matplotlib.image import imread, imsave
import random


def rgb2gray(rgb):
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray



class Img:

    def __init__(self, path):
        """
        Do not change the constructor implementation
        """
        self.path = Path(path)
        self.data = rgb2gray(imread(path)).tolist()

    def save_img(self):
        """
        Do not change the below implementation
        """
        new_path = self.path.with_name(self.path.stem + '_filtered' + self.path.suffix)
        imsave(new_path, self.data, cmap='gray')
        return new_path

    def blur(self, blur_level=16):

        height = len(self.data)
        width = len(self.data[0])
        filter_sum = blur_level ** 2

        result = []
        for i in range(height - blur_level + 1):
            row_result = []
            for j in range(width - blur_level + 1):
                sub_matrix = [row[j:j + blur_level] for row in self.data[i:i + blur_level]]
                average = sum(sum(sub_row) for sub_row in sub_matrix) // filter_sum
                row_result.append(average)
            result.append(row_result)

        self.data = result

    def contour(self):
        for i, row in enumerate(self.data):
            res = []
            for j in range(1, len(row)):
                res.append(abs(row[j-1] - row[j]))

            self.data[i] = res

    def rotate(self):

        # Get the dimensions of the original image
        original_height = len(self.data)
        original_width = len(self.data[0])
        # Create an empty list for the rotated image data
        rotated_data = []

        # Loop through each column in the original image
        for col in range(original_width):
            new_row = []
            # Collect pixels from bottom to top of the column
            for row in range(original_height -1, -1, -1):
                new_row.append(self.data[row][col])
            # Append the new row to the rotated data
            rotated_data.append(new_row)

        # Update the image data with the rotated result
        self.data = rotated_data

    def salt_n_pepper(self):
        # Empty list of row which contains the full picture
        salt_n_pepper_data = []
        zero_to_one_list = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
        # For each value (row) in the large list (Data)
        for row in self.data:
            # Empty list of one row
            new_row = []
            for pixel in row:
                random_number = random.choice(zero_to_one_list)
                if random_number < 0.2:
                    pixel = 255
                elif random_number > 0.8:
                    pixel = 0
                new_row.append(pixel)
            salt_n_pepper_data.append(new_row)

        self.data = salt_n_pepper_data

    def concat(self, other_img):
       try:
        # Get dimensions
        height = len(self.data)
        width = len(self.data[0])
        other_height = len(other_img.data)
        other_width = len(other_img.data[0])

        # Validate that the heights match for horizontal concatenation
        if height != other_height and width != other_width:
            raise RuntimeError

        # Concatenate horizontally
        concatenated_data = []
        for i in range(height):
            concatenated_data.append(self.data[i] + other_img.data[i])


        self.data = concatenated_data
       except ValueError:
           print("other_img is a string. Ensure a valid image object is passed.")



    def segment(self):
        segment_data = []
        for row in self.data:
            # Empty list of one row
            new_row = []
            for pixel in row:
                if pixel > 100:
                    pixel = 255
                else:
                    pixel = 0
                new_row.append(pixel)
            segment_data.append(new_row)
        self.data = segment_data


# my_img = Img('/photos/file_17.jpg')
# another_img = Img('/photos/file_18.jpg')
# my_img.concat(another_img)


# my_img.save_img()


# 8172185006:AAEJyCNJs-9T5aU0fhw_ii34MCDTxAZYRn4
# https://t.me/AshtonyahuBot