"""
Food Image Classifier - Transfer Learning with MobileNetV2
Trains on a subset of food-101 images to classify 40 food categories.
Uses 80 images per class for fast training (~3200 total images).
"""

import os, sys, json, time
# Force UTF-8 for Windows terminal
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import warnings
warnings.filterwarnings('ignore')

# --- Configuration ---
IMAGES_DIR     = os.path.join(os.path.dirname(__file__), '..', 'images')
OUTPUT_DIR     = os.path.join(os.path.dirname(__file__), '..', 'backend')
MODEL_PATH     = os.path.join(OUTPUT_DIR, 'food_classifier.h5')
LABELS_PATH    = os.path.join(OUTPUT_DIR, 'food_classifier_labels.json')
IMG_SIZE       = (128, 128)
BATCH_SIZE     = 32
EPOCHS         = 15
IMGS_PER_CLASS = 80
SEED           = 42

# Mapping food101 categories to freshness model food_type
CATEGORY_TO_FRESHNESS = {
    "apple_pie":          "prepared_meals",
    "baby_back_ribs":     "meat",
    "baklava":            "snacks",
    "beef_carpaccio":     "meat",
    "beef_tartare":       "meat",
    "beet_salad":         "leafy_greens",
    "beignets":           "fried_items",
    "bibimbap":           "prepared_meals",
    "bread_pudding":      "prepared_meals",
    "breakfast_burrito":  "burgers",
    "bruschetta":         "sandwiches",
    "caesar_salad":       "leafy_greens",
    "cannoli":            "snacks",
    "caprese_salad":      "vegetables",
    "carrot_cake":        "prepared_meals",
    "ceviche":            "fish",
    "cheese_plate":       "dairy",
    "cheesecake":         "prepared_meals",
    "chicken_curry":      "prepared_meals",
    "chicken_quesadilla": "prepared_meals",
    "chicken_wings":      "fried_items",
    "chocolate_cake":     "prepared_meals",
    "chocolate_mousse":   "prepared_meals",
    "churros":            "fried_items",
    "clam_chowder":       "prepared_meals",
    "club_sandwich":      "sandwiches",
    "crab_cakes":         "fish",
    "creme_brulee":       "prepared_meals",
    "croque_madame":      "sandwiches",
    "cup_cakes":          "snacks",
    "deviled_eggs":       "prepared_meals",
    "donuts":             "snacks",
    "dumplings":          "prepared_meals",
    "edamame":            "vegetables",
    "eggs_benedict":      "prepared_meals",
    "escargots":          "prepared_meals",
    "falafel":            "fried_items",
    "filet_mignon":       "meat",
    "fish_and_chips":     "fish",
    "foie_gras":          "meat",
}


def prepare_dataset(images_dir, imgs_per_class):
    """Create a balanced subset of the dataset for training."""
    import shutil, random
    random.seed(SEED)

    subset_dir = os.path.join(os.path.dirname(images_dir), 'ml-models', 'image_subset')
    if os.path.exists(subset_dir):
        print(f"  [OK] Reusing existing subset at: {subset_dir}")
        return subset_dir

    print(f"  Creating subset ({imgs_per_class} imgs/class)...")
    os.makedirs(subset_dir, exist_ok=True)

    categories = sorted([d for d in os.listdir(images_dir)
                         if os.path.isdir(os.path.join(images_dir, d))])
    print(f"  Found {len(categories)} categories")

    for cat in categories:
        src_dir = os.path.join(images_dir, cat)
        dst_dir = os.path.join(subset_dir, cat)
        os.makedirs(dst_dir, exist_ok=True)
        imgs = [f for f in os.listdir(src_dir)
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        selected = random.sample(imgs, min(imgs_per_class, len(imgs)))
        for img in selected:
            shutil.copy(os.path.join(src_dir, img), os.path.join(dst_dir, img))

    print(f"  Subset created: {subset_dir}")
    return subset_dir


def build_model(num_classes):
    """Build MobileNetV2 transfer learning model."""
    base_model = MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = BatchNormalization()(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.4)(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.3)(x)
    predictions = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=base_model.input, outputs=predictions)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    return model, base_model


def fine_tune_model(model, base_model, train_gen, val_gen):
    """Unfreeze top 30 layers and fine-tune."""
    for layer in base_model.layers[-30:]:
        layer.trainable = True

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    callbacks = [
        EarlyStopping(monitor='val_accuracy', patience=4, restore_best_weights=True),
        ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2, min_lr=1e-7)
    ]
    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=8,
        callbacks=callbacks,
        verbose=1
    )
    return history


def main():
    print("\n" + "=" * 60)
    print("  [*] Food Image Classifier -- Transfer Learning Training")
    print("=" * 60)
    t0 = time.time()

    print("\n[1/5] Preparing dataset subset...")
    subset_dir = prepare_dataset(IMAGES_DIR, IMGS_PER_CLASS)

    print("\n[2/5] Setting up data generators...")
    train_datagen = ImageDataGenerator(
        rescale=1. / 255,
        validation_split=0.2,
        rotation_range=20,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        zoom_range=0.15,
        brightness_range=[0.8, 1.2]
    )

    train_gen = train_datagen.flow_from_directory(
        subset_dir, target_size=IMG_SIZE, batch_size=BATCH_SIZE,
        class_mode='categorical', subset='training', seed=SEED
    )
    val_gen = train_datagen.flow_from_directory(
        subset_dir, target_size=IMG_SIZE, batch_size=BATCH_SIZE,
        class_mode='categorical', subset='validation', seed=SEED
    )

    class_names = list(train_gen.class_indices.keys())
    num_classes = len(class_names)
    print(f"  Classes: {num_classes}, Train batches: {len(train_gen)}, Val batches: {len(val_gen)}")

    print("\n[3/5] Training with frozen base (feature extraction)...")
    model, base_model = build_model(num_classes)
    callbacks_phase1 = [
        EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True),
        ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6)
    ]
    history1 = model.fit(
        train_gen, validation_data=val_gen,
        epochs=EPOCHS, callbacks=callbacks_phase1, verbose=1
    )
    val_acc_phase1 = max(history1.history['val_accuracy'])
    print(f"\n  Phase 1 best val accuracy: {val_acc_phase1:.4f} ({val_acc_phase1 * 100:.1f}%)")

    print("\n[4/5] Fine-tuning top layers...")
    train_gen2 = train_datagen.flow_from_directory(
        subset_dir, target_size=IMG_SIZE, batch_size=BATCH_SIZE,
        class_mode='categorical', subset='training', seed=SEED
    )
    val_gen2 = train_datagen.flow_from_directory(
        subset_dir, target_size=IMG_SIZE, batch_size=BATCH_SIZE,
        class_mode='categorical', subset='validation', seed=SEED
    )
    history2 = fine_tune_model(model, base_model, train_gen2, val_gen2)
    val_acc_phase2 = max(history2.history['val_accuracy'])
    print(f"\n  Phase 2 best val accuracy: {val_acc_phase2:.4f} ({val_acc_phase2 * 100:.1f}%)")

    print("\n[5/5] Saving model and metadata...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    model.save(MODEL_PATH)
    print(f"  Model saved -> {MODEL_PATH}")

    final_acc = max(val_acc_phase1, val_acc_phase2)
    labels_data = {
        "class_names": class_names,
        "num_classes": num_classes,
        "img_size": list(IMG_SIZE),
        "category_to_freshness": {
            cls: CATEGORY_TO_FRESHNESS.get(cls, "prepared_meals")
            for cls in class_names
        },
        "training_info": {
            "imgs_per_class": IMGS_PER_CLASS,
            "val_accuracy_phase1": round(val_acc_phase1, 4),
            "val_accuracy_phase2": round(val_acc_phase2, 4),
            "final_accuracy": round(final_acc, 4)
        }
    }
    with open(LABELS_PATH, 'w') as f:
        json.dump(labels_data, f, indent=2)
    print(f"  Labels saved -> {LABELS_PATH}")

    elapsed = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"  [DONE] Training complete in {elapsed / 60:.1f} minutes!")
    print(f"  [ACC]  Final validation accuracy: {final_acc * 100:.1f}%")
    print(f"  [FILE] Model: {MODEL_PATH}")
    print(f"  [FILE] Labels: {LABELS_PATH}")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
