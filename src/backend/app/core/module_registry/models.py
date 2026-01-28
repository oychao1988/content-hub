"""
通用模型注册器

提供SQL和MongoDB模型的注册、验证和完整性检查功能
"""

import traceback
from typing import Dict, Any, Optional, Type, List, Callable
from logging import getLogger
from datetime import datetime
from enum import Enum

logger = getLogger(__name__)


class ModelType(Enum):
    """模型类型枚举"""
    SQL = "sql"
    MONGODB = "mongodb"


class ModelVersion:
    """模型版本信息"""

    def __init__(self, version: str, description: str, migration_func: callable = None):
        self.version = version
        self.description = description
        self.migration_func = migration_func
        self.created_at = datetime.utcnow()


class ModelRegistry:
    """数据模型注册管理器"""

    def __init__(self, module_name: str):
        """
        初始化模型注册器
        
        Args:
            module_name: 模块名称（如 "market_evaluation", "product_selection"）
        """
        self.module_name = module_name
        self.sql_models = {}
        self.mongodb_models = {}
        self.model_versions = {}
        self.migration_history = []
        self.validation_rules = {}
        self.integrity_checks = {}

    def register_sql_model(
        self,
        name: str,
        model_class: Type,
        version: str = "1.0.0",
        validation_func: Callable = None,
        integrity_check: Callable = None
    ):
        """注册SQL模型"""
        self.sql_models[name] = {
            'class': model_class,
            'version': version,
            'validation_func': validation_func,
            'integrity_check': integrity_check,
            'registered_at': datetime.utcnow()
        }

        if validation_func:
            self.validation_rules[name] = validation_func

        if integrity_check:
            self.integrity_checks[name] = integrity_check

        logger.info(f"[{self.module_name}] Registered SQL model: {name} v{version}")

    def register_mongodb_model(
        self,
        name: str,
        model_class: Type,
        version: str = "1.0.0",
        validation_func: Callable = None,
        integrity_check: Callable = None
    ):
        """注册MongoDB模型"""
        self.mongodb_models[name] = {
            'class': model_class,
            'version': version,
            'validation_func': validation_func,
            'integrity_check': integrity_check,
            'registered_at': datetime.utcnow()
        }

        if validation_func:
            self.validation_rules[name] = validation_func

        if integrity_check:
            self.integrity_checks[name] = integrity_check

        logger.info(f"[{self.module_name}] Registered MongoDB model: {name} v{version}")

    def add_model_version(self, model_name: str, version: ModelVersion):
        """添加模型版本"""
        if model_name not in self.model_versions:
            self.model_versions[model_name] = []

        self.model_versions[model_name].append(version)
        logger.info(f"[{self.module_name}] Added version {version.version} for model {model_name}")

    def get_model_version(self, model_name: str) -> Optional[str]:
        """获取模型当前版本"""
        if model_name in self.sql_models:
            return self.sql_models[model_name]['version']
        elif model_name in self.mongodb_models:
            return self.mongodb_models[model_name]['version']
        return None

    def validate_model_data(self, model_name: str, data: Dict[str, Any]) -> bool:
        """验证模型数据"""
        if model_name in self.validation_rules:
            try:
                return self.validation_rules[model_name](data)
            except Exception as e:
                logger.error(f"[{self.module_name}] Validation failed for model {model_name}: {e}")
                return False
        return True

    def check_model_integrity(self, model_name: str) -> Dict[str, Any]:
        """检查模型完整性"""
        if model_name in self.integrity_checks:
            try:
                return self.integrity_checks[model_name]()
            except Exception as e:
                logger.error(f"[{self.module_name}] Integrity check failed for model {model_name}: {e}")
                return {'valid': False, 'error': str(e)}
        return {'valid': True, 'message': 'No integrity check defined'}

    def run_migration(self, model_name: str, target_version: str) -> bool:
        """运行模型迁移"""
        if model_name not in self.model_versions:
            logger.warning(f"[{self.module_name}] No versions defined for model {model_name}")
            return False

        versions = self.model_versions[model_name]
        target_version_obj = None

        for version in versions:
            if version.version == target_version:
                target_version_obj = version
                break

        if not target_version_obj:
            logger.error(f"[{self.module_name}] Version {target_version} not found for model {model_name}")
            return False

        if not target_version_obj.migration_func:
            logger.warning(f"[{self.module_name}] No migration function defined for {model_name} v{target_version}")
            return True

        try:
            logger.info(f"[{self.module_name}] Running migration for {model_name} to version {target_version}")
            result = target_version_obj.migration_func()

            if result:
                self.migration_history.append({
                    'model_name': model_name,
                    'version': target_version,
                    'migrated_at': datetime.utcnow(),
                    'success': True
                })
                logger.info(f"[{self.module_name}] Migration completed for {model_name} v{target_version}")
            else:
                logger.error(f"[{self.module_name}] Migration failed for {model_name} v{target_version}")

            return result
        except Exception as e:
            logger.error(f"[{self.module_name}] Migration error for {model_name} v{target_version}: {e}")
            self.migration_history.append({
                'model_name': model_name,
                'version': target_version,
                'migrated_at': datetime.utcnow(),
                'success': False,
                'error': str(e)
            })
            return False

    def get_registry_status(self) -> Dict[str, Any]:
        """获取注册器状态"""
        return {
            'module_name': self.module_name,
            'sql_models': {
                name: {
                    'version': info['version'],
                    'registered_at': info['registered_at'].isoformat(),
                    'has_validation': info['validation_func'] is not None,
                    'has_integrity_check': info['integrity_check'] is not None
                }
                for name, info in self.sql_models.items()
            },
            'mongodb_models': {
                name: {
                    'version': info['version'],
                    'registered_at': info['registered_at'].isoformat(),
                    'has_validation': info['validation_func'] is not None,
                    'has_integrity_check': info['integrity_check'] is not None
                }
                for name, info in self.mongodb_models.items()
            },
            'total_models': len(self.sql_models) + len(self.mongodb_models),
            'migration_history_count': len(self.migration_history),
            'versions_defined': len(self.model_versions)
        }

    def validate_all_models(self) -> Dict[str, Any]:
        """验证所有模型完整性"""
        results = {
            'module_name': self.module_name,
            'sql_models': {},
            'mongodb_models': {},
            'overall_valid': True
        }

        # 检查SQL模型
        for name in self.sql_models:
            integrity_result = self.check_model_integrity(name)
            results['sql_models'][name] = integrity_result
            if not integrity_result.get('valid', False):
                results['overall_valid'] = False

        # 检查MongoDB模型
        for name in self.mongodb_models:
            integrity_result = self.check_model_integrity(name)
            results['mongodb_models'][name] = integrity_result
            if not integrity_result.get('valid', False):
                results['overall_valid'] = False

        return results


def create_model_registry(
    module_name: str,
    sql_models: List[Dict[str, Any]] = None,
    mongodb_models: List[Dict[str, Any]] = None,
    integrity_check_func: Callable = None
) -> ModelRegistry:
    """
    创建并配置模型注册器
    
    Args:
        module_name: 模块名称
        sql_models: SQL模型列表，每项包含 {name, class, version?, validation_func?}
        mongodb_models: MongoDB模型列表，格式同上
        integrity_check_func: 全局完整性检查函数
        
    Returns:
        配置好的ModelRegistry实例
        
    Example:
        registry = create_model_registry(
            module_name="product_selection",
            sql_models=[
                {
                    'name': 'Attribute',
                    'class': Attribute,
                    'version': '1.0.0',
                    'validation_func': validate_attribute
                }
            ],
            integrity_check_func=check_sql_models_integrity
        )
    """
    registry = ModelRegistry(module_name)
    
    # 注册SQL模型
    if sql_models:
        for model_config in sql_models:
            registry.register_sql_model(
                name=model_config['name'],
                model_class=model_config['class'],
                version=model_config.get('version', '1.0.0'),
                validation_func=model_config.get('validation_func'),
                integrity_check=model_config.get('integrity_check')
            )
    
    # 注册MongoDB模型
    if mongodb_models:
        for model_config in mongodb_models:
            registry.register_mongodb_model(
                name=model_config['name'],
                model_class=model_config['class'],
                version=model_config.get('version', '1.0.0'),
                validation_func=model_config.get('validation_func'),
                integrity_check=model_config.get('integrity_check')
            )
    
    # 添加全局完整性检查
    if integrity_check_func:
        registry.integrity_checks["sql_models"] = integrity_check_func
    
    return registry


def get_model_registry_status(registry: ModelRegistry) -> Dict[str, Any]:
    """获取模型注册器状态"""
    return registry.get_registry_status()


def validate_model_data(registry: ModelRegistry, model_name: str, data: Dict[str, Any]) -> bool:
    """验证模型数据"""
    return registry.validate_model_data(model_name, data)


