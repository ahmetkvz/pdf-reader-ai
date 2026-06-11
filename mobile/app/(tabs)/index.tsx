import { Image } from 'expo-image';
import { StyleSheet } from 'react-native';

import { HelloWave } from '@/components/hello-wave';
import ParallaxScrollView from '@/components/parallax-scroll-view';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';

import { useEffect, useMemo, useState } from 'react';
import * as DocumentPicker from 'expo-document-picker';


type PickedPdf = {
  name: string;
  uri: string;
  size?: number;
  mimeType?: string;
};

type UploadResponse =
  | { ok: true; filename: string; size: number; content_type: string }
  | { ok: false; error: string };

export default function HomeScreen() {
  const [ping, setPing] = useState<string>('loading...');
  const [pdf, setPdf] = useState<PickedPdf | null>(null);

  const [uploadStatus, setUploadStatus] = useState<string>('');
  const [uploadedFilename, setUploadedFilename] = useState<string>('');

  const [summaryText, setSummaryText] = useState<string>('');
  const [sensitiveText, setSensitiveText] = useState<string>('');

  // Bilgisayar IP + backend portu
  const API_BASE = useMemo(() => 'http://172.20.10.2:8010', []);

  useEffect(() => {
    fetch(`${API_BASE}/ping`)
      .then((r) => r.json())
      .then((data) => setPing(data?.message ?? 'no message'))
      .catch((e) => setPing('ERROR: ' + String(e)));
  }, [API_BASE]);

  const pickPdf = async () => {
    setUploadStatus('');
    setSummaryText('');
    setSensitiveText('');
    setUploadedFilename('');

    const res = await DocumentPicker.getDocumentAsync({
      type: 'application/pdf',
      copyToCacheDirectory: true,
      multiple: false,
    });

    if (res.canceled) return;

    const a = res.assets?.[0];
    if (!a?.uri) return;

    setPdf({
      name: a.name ?? 'selected.pdf',
      uri: a.uri,
      size: a.size,
      mimeType: a.mimeType,
    });
  };     

const uploadPdf = async () => {
  if (!pdf) {
    setUploadStatus('Önce PDF seç.');
    return;
  }

  try {
    setUploadStatus('Yükleniyor...');
    setSummaryText('');
    setSensitiveText('');
    setUploadedFilename('');

    const formData = new FormData();
    formData.append('file', {
      uri: pdf.uri,
      name: pdf.name || 'selected.pdf',
      type: pdf.mimeType || 'application/pdf',
    } as any);

    const r = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    });

    let body: UploadResponse | any = {};
    try {
      body = await r.json();
    } catch {
      body = { ok: false, error: 'Response is not JSON' };
    }

    if (!r.ok) {
      setUploadStatus(`Upload HTTP ${r.status}: ${body?.error ?? 'unknown'}`);
      return;
    }

    if (body.ok) {
      setUploadedFilename(body.filename);
      setUploadStatus(`Yüklendi ✅ Dosya: ${body.filename} Boyut: ${body.size} byte`);
    } else {
      setUploadStatus(`Upload hata: ${body.error ?? 'unknown'}`);
    }
  } catch (e) {
    setUploadStatus('Upload ERROR: ' + String(e));
  }
};

  const callSummary = async () => {
    if (!uploadedFilename) {
      setSummaryText('Önce PDF’i backend’e yükle (1.1).');
      return;
    }

    try {
      setSummaryText('Özet çıkarılıyor...');
      const r = await fetch(`${API_BASE}/summary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: uploadedFilename }),
      });

      const data = await r.json();
      if (!data?.ok) {
        setSummaryText(`Hata: ${data?.detail ?? data?.error ?? 'unknown'}`);
        return;
      }
      setSummaryText(data.summary ?? '(özet boş)');
    } catch (e) {
      setSummaryText('Summary ERROR: ' + String(e));
    }
  };

  const callSensitive = async () => {
    if (!uploadedFilename) {
      setSensitiveText('Önce PDF’i backend’e yükle (1.1).');
      return;
    }

    try {
      setSensitiveText('Hassas veri taranıyor...');
      const r = await fetch(`${API_BASE}/sensitive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: uploadedFilename }),
      });

      const data = await r.json();
      if (!data?.ok) {
        setSensitiveText(`Hata: ${data?.detail ?? data?.error ?? 'unknown'}`);
        return;
      }

      const findings = data.findings ?? [];
      if (findings.length === 0) {
        setSensitiveText('Bulgu yok ✅');
        return;
      }

      const formatted = findings
        .map(
          (f: any) =>
            `• ${f.type} (adet: ${f.count}) örnek: ${
              Array.isArray(f.samples) ? f.samples.join(', ') : ''
            }`
        )
        .join('\n');

      setSensitiveText(formatted);
    } catch (e) {
      setSensitiveText('Sensitive ERROR: ' + String(e));
    }
  };

  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: '#A1CEDC', dark: '#1D3D47' }}
      headerImage={
        <Image
          source={require('@/assets/images/partial-react-logo.png')}
          style={styles.reactLogo}
        />
      }
    >
      <ThemedView style={styles.stepContainer}>
        <ThemedText type="subtitle">Backend ping: {ping}</ThemedText>
      </ThemedView>

      <ThemedView style={styles.titleContainer}>
        <ThemedText type="title">PDF READER AI</ThemedText>
        <HelloWave />
      </ThemedView>

      <ThemedView style={styles.stepContainer}>
        <ThemedText type="subtitle">Menü</ThemedText>

        <ThemedText onPress={pickPdf}>1) PDF Yükle (Seç)</ThemedText>
        <ThemedText onPress={uploadPdf}>1.1) Seçilen PDF’i Backend’e Yükle</ThemedText>

        <ThemedText onPress={callSummary}>2) Özet Çıkar</ThemedText>
        <ThemedText onPress={callSensitive}>3) Hassas Veri Tespit</ThemedText>
      </ThemedView>

      <ThemedView style={styles.stepContainer}>
        <ThemedText type="subtitle">Seçilen PDF</ThemedText>
        {!pdf ? (
          <ThemedText>Henüz dosya seçilmedi.</ThemedText>
        ) : (
          <>
            <ThemedText>Ad: {pdf.name}</ThemedText>
            <ThemedText>Boyut: {pdf.size ?? '-'} bytes</ThemedText>
          </>
        )}

        {!!uploadedFilename && <ThemedText>Backend dosya adı: {uploadedFilename}</ThemedText>}
        {!!uploadStatus && <ThemedText>Durum: {uploadStatus}</ThemedText>}
      </ThemedView>

      <ThemedView style={styles.stepContainer}>
        <ThemedText type="subtitle">Özet</ThemedText>
        <ThemedText>{summaryText || '—'}</ThemedText>
      </ThemedView>

      <ThemedView style={styles.stepContainer}>
        <ThemedText type="subtitle">Hassas Veri Bulguları</ThemedText>
        <ThemedText>{sensitiveText || '—'}</ThemedText>
      </ThemedView>
    </ParallaxScrollView>
  );
}

const styles = StyleSheet.create({
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  stepContainer: {
    gap: 8,
    marginBottom: 12,
  },
  reactLogo: {
    height: 178,
    width: 290,
    bottom: 0,
    left: 0,
    position: 'absolute',
  },
});
