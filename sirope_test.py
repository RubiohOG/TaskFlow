import sirope
import redis
import datetime

# Clase de prueba
class TestObject:
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.created_at = datetime.datetime.now()
    
    def __str__(self):
        return f"TestObject(name='{self.name}', value={self.value}, created_at={self.created_at})"

# Crear cliente Redis primero
redis_client = redis.Redis(host='localhost', port=6379)
print("Conexión a Redis establecida")

# Inicializar Sirope con el cliente Redis
sir = sirope.Sirope()
print("Conexión establecida con Sirope")

# Crear y guardar un objeto
test_obj = TestObject("test_sirope", 42)
print(f"Objeto creado: {test_obj}")

try:
    # Guardar en Redis
    oid = sir.save(test_obj)
    print(f"Objeto guardado con ID: {oid}")

    # Recuperar de Redis
    retrieved_obj = sir.load(oid)
    print(f"Objeto recuperado: {retrieved_obj}")

    # Verificar que son iguales
    print(f"¿Son iguales name? {test_obj.name == retrieved_obj.name}")
    print(f"¿Son iguales value? {test_obj.value == retrieved_obj.value}")

    print("\nPrueba completada con éxito si todo coincide.")
except Exception as e:
    print(f"Error: {e}") 