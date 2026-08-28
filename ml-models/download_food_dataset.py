"""
Download and Prepare Food Dataset for Training
Matches your 37 specific food types from the dataset
"""

import os
import urllib.request
import zipfile
import shutil
import json
from pathlib import Path
import requests
from tqdm import tqdm

class FoodDatasetDownloader:
    def __init__(self):
        # Your 37 food types
        self.target_foods = [
            'apple', 'banana', 'biryani', 'biscuits', 'broccoli', 'burger', 
            'butter', 'cabbage', 'carrot', 'cheese', 'chicken', 'chips', 
            'cookies', 'egg', 'fish', 'fried_rice', 'fries', 'grapes', 
            'hot_dog', 'kale', 'lettuce', 'mango', 'milk', 'mutton', 
            'namkeen', 'noodles', 'onion', 'orange', 'parsley', 'pasta', 
            'pineapple', 'pizza', 'potato', 'rice', 'sandwich', 'spinach', 
            'tomato', 'watermelon', 'yogurt'
        ]
        
        # Food-101 dataset mapping (matches our target foods)
        self.food101_mapping = {
            'apple': 'apple',
            'banana': 'banana', 
            'broccoli': 'broccoli',
            'burger': 'hamburger',
            'carrot': 'carrot',
            'cheese': 'cheese_plate',
            'chicken': 'chicken_curry',
            'cookies': 'cookies',
            'egg': 'eggs_benedict',
            'fish': 'fish_and_chips',
            'fries': 'french_fries',
            'grapes': 'grapes',
            'hot_dog': 'hot_dog',
            'lettuce': 'caesar_salad',
            'mango': 'mango',
            'onion': 'onion_rings',
            'orange': 'orange',
            'pasta': 'spaghetti_bolognese',
            'pineapple': 'pineapple',
            'pizza': 'pizza',
            'potato': 'french_fries',
            'rice': 'fried_rice',
            'sandwich': 'club_sandwich',
            'spinach': 'spinach',
            'tomato': 'bruschetta',
            'watermelon': 'watermelon'
        }
        
        self.dataset_dir = 'camera_training/dataset'
        self.download_dir = 'downloads'
        
    def download_file(self, url, filename):
        """Download file with progress bar"""
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filename, 'wb') as file, tqdm(
            desc=filename,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)
    
    def download_food101_dataset(self):
        """Download Food-101 dataset"""
        print("=== Downloading Food-101 Dataset ===")
        
        # Create download directory
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Food-101 dataset URL
        food101_url = "http://data.vision.ee.ethz.ch/cvl/food-101.tar.gz"
        tar_path = os.path.join(self.download_dir, 'food-101.tar.gz')
        
        if os.path.exists(tar_path):
            print("Dataset already downloaded!")
            return tar_path
        
        print("Downloading Food-101 dataset (5GB)...")
        print("This may take 10-20 minutes depending on your connection...")
        
        try:
            self.download_file(food101_url, tar_path)
            print("Download completed!")
            return tar_path
        except Exception as e:
            print(f"Download failed: {e}")
            return None
    
    def extract_dataset(self, tar_path):
        """Extract the dataset"""
        print("=== Extracting Dataset ===")
        
        extract_dir = os.path.join(self.download_dir, 'food-101')
        
        if os.path.exists(extract_dir):
            print("Dataset already extracted!")
            return extract_dir
        
        try:
            import tarfile
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(self.download_dir)
            print("Extraction completed!")
            return extract_dir
        except Exception as e:
            print(f"Extraction failed: {e}")
            return None
    
    def copy_matching_foods(self, extract_dir):
        """Copy matching food images to dataset directory"""
        print("=== Organizing Food Images ===")
        
        food101_images_dir = os.path.join(extract_dir, 'food-101', 'images')
        
        if not os.path.exists(food101_images_dir):
            print("Food-101 images directory not found!")
            return
        
        copied_count = 0
        missing_foods = []
        
        for target_food in self.target_foods:
            target_dir = os.path.join(self.dataset_dir, target_food)
            
            # Check if we have a mapping for this food
            if target_food in self.food101_mapping:
                food101_class = self.food101_mapping[target_food]
                source_dir = os.path.join(food101_images_dir, food101_class)
                
                if os.path.exists(source_dir):
                    # Copy images
                    image_files = os.listdir(source_dir)[:100]  # Limit to 100 images per class
                    for img_file in image_files:
                        if img_file.endswith(('.jpg', '.jpeg', '.png')):
                            src_path = os.path.join(source_dir, img_file)
                            dst_path = os.path.join(target_dir, img_file)
                            shutil.copy2(src_path, dst_path)
                            copied_count += 1
                    
                    print(f" Copied {len(image_files)} images for {target_food}")
                else:
                    missing_foods.append(target_food)
                    print(f" No images found for {target_food}")
            else:
                missing_foods.append(target_food)
                print(f" No mapping for {target_food}")
        
        print(f"\n=== Summary ===")
        print(f"Total images copied: {copied_count}")
        print(f"Foods with images: {len(self.target_foods) - len(missing_foods)}")
        print(f"Foods missing: {len(missing_foods)}")
        
        if missing_foods:
            print(f"Missing foods: {', '.join(missing_foods)}")
        
        return copied_count > 0
    
    def create_synthetic_data_for_missing_foods(self):
        """Create placeholder info for missing foods"""
        print("\n=== Handling Missing Foods ===")
        
        # Foods that don't have direct matches in Food-101
        missing_foods = ['biryani', 'biscuits', 'butter', 'cabbage', 'chips', 
                        'fried_rice', 'kale', 'milk', 'mutton', 'namkeen', 
                        'noodles', 'parsley', 'yogurt']
        
        print("The following foods don't have direct matches in Food-101:")
        for food in missing_foods:
            print(f"  - {food}")
        
        print("\nFor these foods, you can:")
        print("1. Add your own images to the folders")
        print("2. Use similar food categories as substitutes")
        print("3. Download images from other sources")
        
        # Create info file
        info_file = os.path.join(self.dataset_dir, 'missing_foods_info.txt')
        with open(info_file, 'w') as f:
            f.write("Missing Foods and Suggestions:\n\n")
            suggestions = {
                'biryani': 'Use fried_rice images',
                'biscuits': 'Use cookies images', 
                'butter': 'Add your own butter images',
                'cabbage': 'Use lettuce images',
                'chips': 'Use french_fries images',
                'fried_rice': 'Use rice images',
                'kale': 'Use spinach images',
                'milk': 'Add your own milk images',
                'mutton': 'Use chicken images',
                'namkeen': 'Use chips images',
                'noodles': 'Use spaghetti images',
                'parsley': 'Use spinach images',
                'yogurt': 'Add your own yogurt images'
            }
            
            for food, suggestion in suggestions.items():
                f.write(f"{food}: {suggestion}\n")
        
        print(f"\nCreated info file: {info_file}")
    
    def download_alternative_dataset(self):
        """Try to download additional food images"""
        print("\n=== Downloading Additional Food Images ===")
        
        # This would be a placeholder for downloading from other sources
        # For now, we'll create a simple guide
        
        guide_file = os.path.join(self.dataset_dir, 'image_collection_guide.md')
        with open(guide_file, 'w') as f:
            f.write("# Food Image Collection Guide\n\n")
            f.write("## Missing Foods\n\n")
            f.write("For these foods, you can collect images:\n\n")
            
            missing_foods = ['biryani', 'biscuits', 'butter', 'cabbage', 'chips', 
                           'fried_rice', 'kale', 'milk', 'mutton', 'namkeen', 
                           'noodles', 'parsley', 'yogurt']
            
            for food in missing_foods:
                f.write(f"### {food.title()}\n")
                f.write(f"- Add 50+ images to `{food}/` folder\n")
                f.write(f"- Images should be clear and well-lit\n")
                f.write(f"- Different angles and backgrounds\n")
                f.write(f"- Size: 224x224 or larger\n\n")
        
        print(f"Created collection guide: {guide_file}")
    
    def run(self):
        """Main download and preparation process"""
        print("=== FreshSense Food Dataset Downloader ===")
        print(f"Target foods: {len(self.target_foods)}")
        
        # Step 1: Download dataset
        tar_path = self.download_food101_dataset()
        if not tar_path:
            print("Failed to download dataset!")
            return False
        
        # Step 2: Extract dataset
        extract_dir = self.extract_dataset(tar_path)
        if not extract_dir:
            print("Failed to extract dataset!")
            return False
        
        # Step 3: Copy matching foods
        success = self.copy_matching_foods(extract_dir)
        
        # Step 4: Handle missing foods
        self.create_synthetic_data_for_missing_foods()
        self.download_alternative_dataset()
        
        # Step 5: Summary
        print("\n=== Download Complete ===")
        print("Dataset is ready for training!")
        print("\nNext steps:")
        print("1. Add images for missing foods if desired")
        print("2. Run: python camera_model_trainer.py")
        
        return success

def main():
    """Main function"""
    downloader = FoodDatasetDownloader()
    downloader.run()

if __name__ == "__main__":
    main()
