"""Decodifica áudio de verdade para detectar incompatibilidades entre Whisper e PyAV."""

from array import array
from io import BytesIO
import math
import unittest
import wave

from faster_whisper.audio import decode_audio


def criar_wav(taxa=16000, canais=1):
    amostras = array("h")
    for indice in range(taxa):
        valor = int(8000 * math.sin(2 * math.pi * 440 * indice / taxa))
        amostras.extend([valor] * canais)
    arquivo = BytesIO()
    with wave.open(arquivo, "wb") as gravacao:
        gravacao.setnchannels(canais)
        gravacao.setsampwidth(2)
        gravacao.setframerate(taxa)
        gravacao.writeframes(amostras.tobytes())
    arquivo.seek(0)
    return arquivo


class DecodificacaoAudioTests(unittest.TestCase):
    def test_abre_wav_sem_erro_metadata_errors(self):
        audio = decode_audio(criar_wav(), sampling_rate=16000)
        self.assertEqual(audio.shape, (16000,))
        self.assertEqual(str(audio.dtype), "float32")
        self.assertGreater(float(abs(audio).max()), 0.1)

    def test_converte_estereo_e_taxa_de_amostragem(self):
        audio = decode_audio(criar_wav(taxa=44100, canais=2), sampling_rate=16000)
        self.assertEqual(audio.shape, (16000,))
        self.assertGreater(float(abs(audio).max()), 0.1)


if __name__ == "__main__":
    unittest.main()
