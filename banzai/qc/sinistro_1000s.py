import numpy as np
import os

from banzai.stages import Stage
from banzai import logs


class ThousandsTest(Stage):
    """
    Reject any images that have 20% or more of their pixels exactly equal to 1000.

    Notes
    =====
    When the Sinistro camera gets into a weird state, sometimes it just produces electrical noise
    in the images. When that happens, a large fraction of the pixels are set exactly to the value
    1000.
    """
    # Empirically we have decided that if 20% of the image exactly equals 1000
    # something bad probably happened, so we reject the image
    THOUSANDS_THRESHOLD = 0.2

    def __init__(self, pipeline_context):
        super(ThousandsTest, self).__init__(pipeline_context)

    @property
    def group_by_keywords(self):
        return None

    def do_stage(self, images):
        images_to_remove = []
        for image in images:
            npixels = np.product(image.data.shape)
            fraction_1000s = float(np.sum(image.data == 1000)) / npixels
            logging_tags = logs.image_config_to_tags(image, self.group_by_keywords)
            logs.add_tag(logging_tags, 'filename', os.path.basename(image.filename))
            logs.add_tag(logging_tags, 'FRAC1000', fraction_1000s)
            logs.add_tag(logging_tags, 'threshold', self.THOUSANDS_THRESHOLD)
            has_1000s_error = fraction_1000s > self.THOUSANDS_THRESHOLD
            qc_results = {'sinistro_thousands.failed': has_1000s_error,
                          'sinistro_thousands.fraction': fraction_1000s,
                          'sinistro_thousands.threshold': self.THOUSANDS_THRESHOLD}
            if has_1000s_error:
                self.logger.error('Image is mostly 1000s. Rejecting image', extra=logging_tags)
                qc_results['rejected'] = True
                images_to_remove.append(image)
            else:
                self.logger.info('Measuring fraction of 1000s.', extra=logging_tags)
            self.save_qc_results(qc_results, image)
        for image in images_to_remove:
            images.remove(image)

        return images
