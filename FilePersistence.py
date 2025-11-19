"""
File-based Model Persistence (No Database Required!)
Saves models and data to local files
"""
import pickle
import logging
import os
import shutil
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileModelPersistence:
    """
    File-based persistence for ML models
    No database required - everything stored in files
    """
    
    def __init__(self, storage_dir="models/storage"):
        """
        Initialize file-based persistence
        
        Args:
            storage_dir: Directory to store model files
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # File paths
        self.model_file = os.path.join(storage_dir, "current_model.pkl")
        self.backup_dir = os.path.join(storage_dir, "backups")
        self.metadata_file = os.path.join(storage_dir, "model_metadata.json")
        
        os.makedirs(self.backup_dir, exist_ok=True)
        
        logger.info(f"✅ File-based persistence initialized at: {storage_dir}")
    
    def save_model(self, model):
        """
        Save model to file with automatic backup
        
        Args:
            model: The model to save (any picklable object)
        """
        try:
            # Create backup of existing model if it exists
            if os.path.exists(self.model_file):
                self._create_backup()
            
            # Save new model
            with open(self.model_file, 'wb') as f:
                pickle.dump(model, f)
            
            # Update metadata
            self._update_metadata()
            
            logger.info(f"✅ Model saved to: {self.model_file}")
            
        except Exception as e:
            logger.error(f"❌ Error saving model: {e}")
            raise
    
    def load_model(self):
        """
        Load model from file
        
        Returns:
            Loaded model or None if not found
        """
        if not os.path.exists(self.model_file):
            logger.info("ℹ️ No saved model found")
            return None
        
        try:
            with open(self.model_file, 'rb') as f:
                model = pickle.load(f)
            
            logger.info(f"✅ Model loaded from: {self.model_file}")
            return model
            
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            logger.info("ℹ️ Will create new model")
            return None
    
    def _create_backup(self):
        """Create timestamped backup of current model"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"model_backup_{timestamp}.pkl")
            
            shutil.copy2(self.model_file, backup_file)
            logger.info(f"📦 Backup created: {backup_file}")
            
            # Keep only last 5 backups
            self._cleanup_old_backups(keep=5)
            
        except Exception as e:
            logger.warning(f"⚠️ Could not create backup: {e}")
    
    def _cleanup_old_backups(self, keep=5):
        """Keep only the N most recent backups"""
        try:
            backups = sorted(
                [f for f in os.listdir(self.backup_dir) if f.endswith('.pkl')],
                reverse=True
            )
            
            # Delete old backups
            for old_backup in backups[keep:]:
                old_path = os.path.join(self.backup_dir, old_backup)
                os.remove(old_path)
                logger.info(f"🗑️ Deleted old backup: {old_backup}")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not cleanup backups: {e}")
    
    def _update_metadata(self):
        """Update model metadata file"""
        try:
            metadata = {
                "last_saved": datetime.now().isoformat(),
                "model_file": self.model_file,
                "file_size_bytes": os.path.getsize(self.model_file),
                "backup_count": len([f for f in os.listdir(self.backup_dir) if f.endswith('.pkl')])
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Could not update metadata: {e}")
    
    def get_metadata(self):
        """Get model metadata"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def list_backups(self):
        """List all available backups"""
        try:
            backups = sorted(
                [f for f in os.listdir(self.backup_dir) if f.endswith('.pkl')],
                reverse=True
            )
            return backups
        except:
            return []
    
    def restore_from_backup(self, backup_name):
        """
        Restore model from a specific backup
        
        Args:
            backup_name: Name of the backup file
        """
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if not os.path.exists(backup_path):
                logger.error(f"❌ Backup not found: {backup_name}")
                return False
            
            # Backup current model before restoring
            if os.path.exists(self.model_file):
                self._create_backup()
            
            # Restore from backup
            shutil.copy2(backup_path, self.model_file)
            logger.info(f"✅ Model restored from backup: {backup_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error restoring backup: {e}")
            return False
    
    def get_storage_info(self):
        """Get information about storage usage"""
        try:
            model_size = os.path.getsize(self.model_file) if os.path.exists(self.model_file) else 0
            
            backup_sizes = []
            for backup in os.listdir(self.backup_dir):
                if backup.endswith('.pkl'):
                    backup_path = os.path.join(self.backup_dir, backup)
                    backup_sizes.append(os.path.getsize(backup_path))
            
            total_backup_size = sum(backup_sizes)
            
            return {
                "storage_directory": self.storage_dir,
                "model_size_bytes": model_size,
                "model_size_mb": round(model_size / (1024 * 1024), 2),
                "backup_count": len(backup_sizes),
                "total_backup_size_bytes": total_backup_size,
                "total_backup_size_mb": round(total_backup_size / (1024 * 1024), 2),
                "total_size_mb": round((model_size + total_backup_size) / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting storage info: {e}")
            return {}

