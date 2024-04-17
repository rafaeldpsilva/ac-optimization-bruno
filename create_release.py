import os
import zipfile


def zip_selected_folders(zip_file_path, folders_to_zip):
    try:
        with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
            for folder in folders_to_zip:
                if os.path.isdir(folder):
                    for foldername, subfolders, filenames in os.walk(folder):
                        for filename in filenames:
                            file_path = os.path.join(foldername, filename)
                            zip_file.write(file_path, file_path)
                else:
                    print(f"Ignoring non-directory item: {folder}")

            # add requirments
            zip_file.write("requirements.txt", "requirements.txt")

        print(f"Zip file created successfully: {zip_file_path}")

    except Exception as e:
        print(f"Error creating zip file: {e}")


# Example Usage
zip_file_path = "iot-bm.zip"
folders_to_zip = ["api", "core", "database", "model", "modules", "services", "utils", "saved_model"]

zip_selected_folders(zip_file_path, folders_to_zip)
