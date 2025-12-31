import numpy as np
from scipy.spatial.distance import euclidean

class LipSyncEvaluator:
    """DTW 및 랜드마크 비교를 통한 립싱크 정합도 평가 모듈"""

    def calculate_dtw_distance(self, audio_envelope, lip_opening_sequence):
        """Dynamic Time Warping을 이용한 음성-입모양 동기화 거리 측정"""
        n, m = len(audio_envelope), len(lip_opening_sequence)
        dtw_matrix = np.zeros((n+1, m+1))
        dtw_matrix[1:, 0] = np.inf
        dtw_matrix[0, 1:] = np.inf

        for i in range(1, n+1):
            for j in range(1, m+1):
                cost = abs(audio_envelope[i-1] - lip_opening_sequence[j-1])
                dtw_matrix[i, j] = cost + min(dtw_matrix[i-1, j],    # insertion
                                            dtw_matrix[i, j-1],    # deletion
                                            dtw_matrix[i-1, j-1])  # match
        
        return dtw_matrix[n, m] / (n + m)  # 정규화된 거리

    def evaluate_landmark_consistency(self, ref_landmarks, gen_landmarks):
        """랜드마크 유클리드 거리를 통한 시각적 정밀도 측정"""
        distances = [euclidean(r, g) for r, g in zip(ref_landmarks, gen_landmarks)]
        return np.mean(distances)

if __name__ == "__main__":
    evaluator = LipSyncEvaluator()
    print("Lip-sync Evaluator (DTW/CNN-Landmark) ready.")
