"""
Create Sample Food Images for Training
Uses existing images from your project and creates synthetic training data
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import json
import random

class SampleImageCreator:
    def __init__(self):
        self.dataset_dir = 'camera_training/dataset'
        self.target_foods = [
            'apple', 'banana', 'biryani', 'biscuits', 'broccoli', 'burger', 
            'butter', 'cabbage', 'carrot', 'cheese', 'chicken', 'chips', 
            'cookies', 'egg', 'fish', 'fried_rice', 'fries', 'grapes', 
            'hot_dog', 'kale', 'lettuce', 'mango', 'milk', 'mutton', 
            'namkeen', 'noodles', 'onion', 'orange', 'parsley', 'pasta', 
            'pineapple', 'pizza', 'potato', 'rice', 'sandwich', 'spinach', 
            'tomato', 'watermelon', 'yogurt'
        ]
        
        # Simple food colors and shapes for synthetic images
        self.food_templates = {
            'apple': {'color': (255, 0, 0), 'shape': 'circle'},
            'banana': {'color': (255, 255, 0), 'shape': 'ellipse'},
            'orange': {'color': (0, 165, 255), 'shape': 'circle'},
            'tomato': {'color': (255, 99, 71), 'shape': 'circle'},
            'lettuce': {'color': (0, 255, 0), 'shape': 'ellipse'},
            'cheese': {'color': (255, 255, 0), 'shape': 'rectangle'},
            'bread': {'color': (255, 200, 100), 'shape': 'rectangle'},
            'egg': {'color': (255, 255, 255), 'shape': 'ellipse'},
            'chicken': {'color': (255, 150, 150), 'shape': 'rectangle'},
            'fish': {'color': (100, 150, 255), 'shape': 'ellipse'},
            'rice': {'color': (255, 255, 255), 'shape': 'rectangle'},
            'potato': {'color': (255, 200, 150), 'shape': 'ellipse'},
            'onion': {'color': (255, 200, 200), 'shape': 'circle'},
            'carrot': {'color': (255, 140, 0), 'shape': 'rectangle'},
            'grapes': {'color': (128, 0, 128), 'shape': 'circle'},
        }
    
    def create_synthetic_food_image(self, food_name, img_size=(128, 128), variation=0):
        """Create a synthetic food image"""
        img = Image.new('RGB', img_size, (240, 240, 240))  # Light gray background
        
        # Get food template or use default
        template = self.food_templates.get(food_name, {'color': (100, 100, 100), 'shape': 'circle'})
        
        # Create main food shape
        if template['shape'] == 'circle':
            size = int(60 + variation * 20)
            pos = (img_size[0]//2 - size//2, img_size[1]//2 - size//2)
            draw = Image.new('RGB', (size, size), template['color'])
            mask = Image.new('L', (size, size), 255)
            img.paste(draw, pos, mask)
            
        elif template['shape'] == 'ellipse':
            width = int(80 + variation * 20)
            height = int(60 + variation * 15)
            pos = (img_size[0]//2 - width//2, img_size[1]//2 - height//2)
            draw = Image.new('RGB', (width, height), template['color'])
            mask = Image.new('L', (width, height), 255)
            img.paste(draw, pos, mask)
            
        elif template['shape'] == 'rectangle':
            width = int(70 + variation * 20)
            height = int(50 + variation * 15)
            pos = (img_size[0]//2 - width//2, img_size[1]//2 - height//2)
            draw = Image.new('RGB', (width, height), template['color'])
            img.paste(draw, pos)
        
        # Add some texture/noise
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(0.8 + random.random() * 0.4)
        
        # Add slight color variation
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.9 + random.random() * 0.2)
        
        # Add some noise/grain
        img_array = np.array(img)
        noise = np.random.normal(0, 5, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255)
        
        return Image.fromarray(img_array.astype(np.uint8))
    
    def create_food_variations(self, food_name, num_images=20):
        """Create variations of food images"""
        images = []
        
        for i in range(num_images):
            variation = random.random()
            img = self.create_synthetic_food_image(food_name, variation=variation)
            
            # Apply random transformations
            if random.random() > 0.5:
                # Random rotation
                angle = random.uniform(-15, 15)
                img = img.rotate(angle, expand=False, fillcolor=(240, 240, 240))
            
            if random.random() > 0.7:
                # Random blur
                img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5, 1.5)))
            
            if random.random() > 0.8:
                # Brightness variation
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(0.8 + random.random() * 0.4)
            
            images.append(img)
        
        return images
    
    def create_all_food_images(self):
        """Create synthetic images for all food types"""
        print("=== Creating Synthetic Food Images ===")
        
        total_created = 0
        
        for food_name in self.target_foods:
            food_dir = os.path.join(self.dataset_dir, food_name)
            
            # Create variations
            images = self.create_food_variations(food_name, num_images=30)
            
            # Save images
            for i, img in enumerate(images):
                filename = os.path.join(food_dir, f"{food_name}_{i+1:03d}.jpg")
                img.save(filename, 'JPEG', quality=85)
                total_created += 1
            
            print(f"Created {len(images)} images for {food_name}")
        
        print(f"\nTotal images created: {total_created}")
        return total_created
    
    def create_info_file(self):
        """Create information file about synthetic dataset"""
        info_file = os.path.join(self.dataset_dir, 'dataset_info.txt')
        
        with open(info_file, 'w') as f:
            f.write("=== FreshSense Synthetic Food Dataset ===\n\n")
            f.write(f"Total food categories: {len(self.target_foods)}\n")
            f.write(f"Images per category: 30\n")
            f.write(f"Total images: {len(self.target_foods) * 30}\n")
            f.write(f"Image size: 128x128\n")
            f.write(f"Format: JPEG\n\n")
            f.write("Note: This is a synthetic dataset for testing.\n")
            f.write("For production use, replace with real food images.\n\n")
            f.write("Food Categories:\n")
            for food in self.target_foods:
                f.write(f"- {food}\n")
        
        print(f"Created info file: {info_file}")
    
    def run(self):
        """Main creation process"""
        print("=== FreshSense Synthetic Dataset Creator ===")
        
        # Create all food images
        total_images = self.create_all_food_images()
        
        # Create info file
        self.create_info_file()
        
        print("\n=== Dataset Creation Complete ===")
        print(f"Ready for training with {total_images} images!")
        print("\nNext steps:")
        print("1. Run: python camera_model_trainer.py")
        print("2. This will train on synthetic data")
        print("3. Later replace with real food images for better accuracy")

def main():
    """Main function"""
    creator = SampleImageCreator()
    creator.run()

if __name__ == "__main__":
    main()
