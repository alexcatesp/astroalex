"""
Machine Learning Quality Control using Isolation Forest
"""
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder


class QualityControl:
    """
    ML-based quality control using Isolation Forest

    Detects anomalies in:
    - FWHM (seeing variations, wind)
    - Eccentricity (tracking issues)
    - Background level (clouds, light pollution)
    - Star count (clouds, transparency)
    """

    def __init__(self, contamination: float = 0.1):
        """
        Args:
            contamination: Expected fraction of outliers (default 10%)
        """
        self.contamination = contamination
        self.scaler = StandardScaler()
        self.model = None

    def analyze_session(self, frame_paths: List[str]) -> Dict:
        """
        Analyze a complete imaging session

        Args:
            frame_paths: List of paths to FITS frames

        Returns:
            Dict with analysis results and rejection recommendations
        """
        # Extract features from all frames
        features_list = []
        frame_info = []

        for frame_path in frame_paths:
            try:
                features = self._extract_features(frame_path)
                features_list.append(features)
                frame_info.append({
                    'path': frame_path,
                    'features': features
                })
            except Exception as e:
                print(f"Error processing {frame_path}: {e}")
                continue

        if len(features_list) < 10:
            return {
                'error': 'Not enough frames for analysis (minimum 10 required)',
                'frame_count': len(features_list)
            }

        # Convert to numpy array
        X = np.array([[
            f['fwhm'],
            f['eccentricity'],
            f['background'],
            f['star_count'],
            f['background_std']
        ] for f in features_list])

        # Normalize features
        X_scaled = self.scaler.fit_transform(X)

        # Train Isolation Forest
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        predictions = self.model.fit_predict(X_scaled)

        # Analyze results
        rejected_indices = np.where(predictions == -1)[0]
        accepted_indices = np.where(predictions == 1)[0]

        # Categorize rejections
        rejection_reasons = self._categorize_rejections(
            features_list,
            rejected_indices
        )

        # Build report
        report = {
            'total_frames': len(frame_paths),
            'accepted': len(accepted_indices),
            'rejected': len(rejected_indices),
            'rejection_percentage': (len(rejected_indices) / len(frame_paths)) * 100,
            'rejected_frames': [
                {
                    'path': frame_info[i]['path'],
                    'reason': rejection_reasons[j],
                    'features': frame_info[i]['features']
                }
                for j, i in enumerate(rejected_indices)
            ],
            'accepted_frames': [
                frame_info[i]['path'] for i in accepted_indices
            ],
            'statistics': self._calculate_statistics(features_list, accepted_indices)
        }

        return report

    def _extract_features(self, frame_path: str) -> Dict:
        """
        Extract quality metrics from a frame

        Returns:
            Dict with features: fwhm, eccentricity, background, star_count, etc.
        """
        with fits.open(frame_path) as hdul:
            data = hdul[0].data.astype(float)

        # Background statistics
        mean, median, std = sigma_clipped_stats(data, sigma=3.0)

        # Star detection
        try:
            daofind = DAOStarFinder(fwhm=3.0, threshold=5.0 * std)
            sources = daofind(data - median)

            if sources is None or len(sources) == 0:
                fwhm = 0
                eccentricity = 0
                star_count = 0
            else:
                # FWHM statistics
                fwhm = np.median(sources['fwhm'])

                # Eccentricity (roundness metric)
                if 'roundness' in sources.colnames:
                    eccentricity = 1.0 - np.median(sources['roundness'])
                else:
                    eccentricity = 0

                star_count = len(sources)

        except Exception:
            fwhm = 0
            eccentricity = 0
            star_count = 0

        return {
            'fwhm': float(fwhm),
            'eccentricity': float(eccentricity),
            'background': float(median),
            'background_std': float(std),
            'star_count': int(star_count)
        }

    def _categorize_rejections(
        self,
        features_list: List[Dict],
        rejected_indices: np.ndarray
    ) -> List[str]:
        """
        Categorize why frames were rejected

        Returns:
            List of rejection reasons
        """
        reasons = []

        # Calculate session medians for comparison
        all_fwhm = [f['fwhm'] for f in features_list if f['fwhm'] > 0]
        all_bg = [f['background'] for f in features_list]
        all_stars = [f['star_count'] for f in features_list]

        median_fwhm = np.median(all_fwhm) if all_fwhm else 0
        median_bg = np.median(all_bg)
        median_stars = np.median(all_stars)

        for idx in rejected_indices:
            f = features_list[idx]

            # Determine primary reason
            if f['fwhm'] > median_fwhm * 1.5:
                reasons.append("Poor seeing (high FWHM)")
            elif f['eccentricity'] > 0.3:
                reasons.append("Tracking error (elongated stars)")
            elif f['background'] > median_bg * 1.3:
                reasons.append("High background (clouds/light pollution)")
            elif f['star_count'] < median_stars * 0.6:
                reasons.append("Low star count (clouds/transparency)")
            else:
                reasons.append("Anomalous (multiple factors)")

        return reasons

    def _calculate_statistics(
        self,
        features_list: List[Dict],
        accepted_indices: np.ndarray
    ) -> Dict:
        """Calculate statistics for accepted frames"""
        accepted_features = [features_list[i] for i in accepted_indices]

        fwhm_values = [f['fwhm'] for f in accepted_features if f['fwhm'] > 0]
        bg_values = [f['background'] for f in accepted_features]
        star_counts = [f['star_count'] for f in accepted_features]

        return {
            'fwhm': {
                'median': float(np.median(fwhm_values)) if fwhm_values else 0,
                'std': float(np.std(fwhm_values)) if fwhm_values else 0
            },
            'background': {
                'median': float(np.median(bg_values)),
                'std': float(np.std(bg_values))
            },
            'star_count': {
                'median': float(np.median(star_counts)),
                'std': float(np.std(star_counts))
            }
        }

    def move_rejected_frames(self, report: Dict, rejected_dir: Path):
        """
        Move rejected frames to a separate directory

        Args:
            report: QC report from analyze_session()
            rejected_dir: Directory to move rejected frames to
        """
        import shutil

        rejected_dir.mkdir(parents=True, exist_ok=True)

        for item in report['rejected_frames']:
            source = Path(item['path'])
            if source.exists():
                dest = rejected_dir / source.name
                shutil.move(str(source), str(dest))
                print(f"Moved {source.name} -> {rejected_dir} (Reason: {item['reason']})")
