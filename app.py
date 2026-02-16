import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  Alert,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

/* ================= LOGIN ================= */

const USER = "admin";
const PASS = "1234";

/* ================= APP ================= */

export default function App() {
  const [logged, setLogged] = useState(false);
  const [user, setUser] = useState("");
  const [pass, setPass] = useState("");

  const [databases, setDatabases] = useState([]);
  const [newDB, setNewDB] = useState("");
  const [selectedDB, setSelectedDB] = useState(null);

  /* ===== CARGAR BASES GUARDADAS ===== */

  useEffect(() => {
    loadDatabases();
  }, []);

  const loadDatabases = async () => {
    const data = await AsyncStorage.getItem("DATABASES");
    if (data) {
      setDatabases(JSON.parse(data));
    }
  };

  /* ===== GUARDAR BASES ===== */

  const saveDatabases = async (list) => {
    await AsyncStorage.setItem("DATABASES", JSON.stringify(list));
    setDatabases(list);
  };

  /* ===== LOGIN ===== */

  const login = () => {
    if (user === USER && pass === PASS) {
      setLogged(true);
    } else {
      Alert.alert("Error", "Usuario o contraseña incorrectos");
    }
  };

  /* ===== CREAR BASE ===== */

  const createDatabase = () => {
    if (!newDB.trim()) return;

    const updated = [...databases, newDB];
    saveDatabases(updated);
    setNewDB("");

    Alert.alert(
      "Base creada",
      `Se guardó en el celular como:\n${newDB}`
    );
  };

  /* ===== SELECCIONAR BASE ===== */

  const selectDatabase = async (name) => {
    setSelectedDB(name);
    await AsyncStorage.setItem("ACTIVE_DB", name);
  };

  /* ================= LOGIN SCREEN ================= */

  if (!logged) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Iniciar Sesión</Text>

        <TextInput
          placeholder="Usuario"
          style={styles.input}
          value={user}
          onChangeText={setUser}
        />

        <TextInput
          placeholder="Contraseña"
          secureTextEntry
          style={styles.input}
          value={pass}
          onChangeText={setPass}
        />

        <TouchableOpacity style={styles.button} onPress={login}>
          <Text style={styles.buttonText}>Entrar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  /* ================= PANEL PRINCIPAL ================= */

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Gestor de Bases</Text>

      <Text style={{ marginBottom: 10 }}>
        Base activa: {selectedDB || "Ninguna"}
      </Text>

      {/* CREAR BASE */}
      <TextInput
        placeholder="Nombre nueva base"
        style={styles.input}
        value={newDB}
        onChangeText={setNewDB}
      />

      <TouchableOpacity style={styles.button} onPress={createDatabase}>
        <Text style={styles.buttonText}>Crear Base</Text>
      </TouchableOpacity>

      {/* LISTA BASES */}
      <FlatList
        data={databases}
        keyExtractor={(item, index) => index.toString()}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.dbItem}
            onPress={() => selectDatabase(item)}
          >
            <Text style={{ color: "white" }}>{item}</Text>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

/* ================= ESTILOS ================= */

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#111",
    padding: 20,
    justifyContent: "center",
  },
  title: {
    fontSize: 24,
    color: "white",
    marginBottom: 20,
    textAlign: "center",
  },
  input: {
    backgroundColor: "white",
    padding: 12,
    borderRadius: 8,
    marginBottom: 10,
  },
  button: {
    backgroundColor: "#25D366",
    padding: 15,
    borderRadius: 10,
    alignItems: "center",
    marginBottom: 20,
  },
  buttonText: {
    color: "white",
    fontWeight: "bold",
  },
  dbItem: {
    backgroundColor: "#333",
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
  },
});

