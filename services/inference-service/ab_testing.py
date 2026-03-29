"""
A/B Testing for Model Versions.

Routes traffic between champion and challenger models.
"""

import os
import random
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ABTestRouter:
    """
    Routes inference requests between model versions.
    """

    def __init__(self):
        self.enabled = os.getenv('AB_TEST_ENABLED', 'false').lower() == 'true'
        self.champion_version = os.getenv('AB_TEST_CHAMPION_VERSION', 'v1.0')
        self.challenger_version = os.getenv('AB_TEST_CHALLENGER_VERSION', 'v2.0')
        self.challenger_traffic = int(os.getenv('AB_TEST_CHALLENGER_TRAFFIC', '10'))

        logger.info(
            f'A/B Testing: enabled={self.enabled}, '
            f'champion={self.champion_version}, challenger={self.challenger_version}, '
            f'challenger_traffic={self.challenger_traffic}%'
        )

    def get_model_version(self, patient_id: Optional[int] = None) -> str:
        if not self.enabled:
            return self.champion_version

        if patient_id is not None:
            random.seed(patient_id)

        if random.randint(1, 100) <= self.challenger_traffic:
            return self.challenger_version
        else:
            return self.champion_version


ab_router = ABTestRouter()


def get_model_version(patient_id: Optional[int] = None) -> str:
    return ab_router.get_model_version(patient_id)
