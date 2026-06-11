import { useState } from "react";
import { Button, StyleSheet, View } from "react-native";
import * as DocumentPicker from "expo-document-picker";
import { ThemedText } from "@/components/themed-text";
import { ThemedView } from "@/components/themed-view";

export default function UploadScreen() {
  const [fileName, setFileName] = useState<string>("Seçilmedi");

  const pickPdf = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: ["application/pdf"],
      copyToCacheDirectory: true,
      multiple: false,
    });

    if (result.canceled) return;

    const file = result.assets[0];
    setFileName(file.name);

    // Şimdilik sadece seçimi gösteriyoruz.
    // Bir sonraki adımda buradan backende upload edeceğiz.
  };

  return (
    <ThemedView style={styles.container}>
      <ThemedText type="title">PDF Yükle</ThemedText>

      <View style={{ height: 12 }} />

      <ThemedText>Seçilen dosya: {fileName}</ThemedText>

      <View style={{ height: 12 }} />

      <Button title="PDF Seç" onPress={pickPdf} />
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, gap: 8 },
});
