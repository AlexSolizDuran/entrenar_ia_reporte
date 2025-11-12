import json
from datasets import load_dataset, DatasetDict
from transformers import (
    T5ForConditionalGeneration,
    T5Tokenizer,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    DataCollatorForSeq2Seq,
)

# ... (El código de las funciones y constantes queda igual, solo se encapsula) ...

# --- CÓDIGO NUEVO ---
if __name__ == '__main__':
# --- TODO EL CÓDIGO RESTANTE DEBE IR DENTRO DE ESTE BLOQUE ---

    # --- 1. Definir Constantes ---
    # El nombre del modelo T5 base que descargaremos.
    MODELO_BASE = "t5-small"
    # El nombre de tu archivo de datos generado
    ARCHIVO_DATOS = "train.jsonl" 
    # El nombre de la carpeta donde se guardará tu IA entrenada
    CARPETA_MODELO_FINAL = "./mi-modelo-entrenado"

    # --- 2. Cargar y Pre-procesar el Dataset ---

    print("Cargando y pre-procesando el dataset...")

    # Carga tu archivo train.jsonl
    dataset = load_dataset("json", data_files=ARCHIVO_DATOS)

    # La columna de entrada que creamos en el generador
    columna_input = "texto"
    # La columna de salida que creamos
    columna_output = "salida_json"

    # Cargar el "tokenizador" de T5. Este convierte el texto en números que la IA entiende.
    tokenizer = T5Tokenizer.from_pretrained(MODELO_BASE)

    def preprocess_function(examples):
        """
        Función que convierte el texto de entrada y salida
        en "tokens" (números) que T5 puede entender.
        """
        # Tokeniza las entradas (los prompts)
        inputs = tokenizer(
            examples[columna_input], 
            max_length=512,  # Longitud máxima de un prompt
            truncation=True, 
            padding="max_length"
        )

        # Tokeniza las salidas (el JSON con el SQL)
        # Usamos 'as_target_tokenizer' para las salidas
        with tokenizer.as_target_tokenizer():
            labels = tokenizer(
                examples[columna_output], 
                max_length=512, # Longitud máxima del SQL+JSON
                truncation=True, 
                padding="max_length"
            )

        # El modelo necesita la columna 'labels' para saber qué debe predecir
        inputs["labels"] = labels["input_ids"]
        return inputs

    # Aplica esta función a todo el dataset
    dataset_tokenizado = dataset.map(preprocess_function, batched=True)

    # Opcional: Dividir en entrenamiento (90%) y validación (10%)
    # Esto ayuda a saber si el modelo está aprendiendo bien o solo memorizando.
    split_dataset = dataset_tokenizado["train"].train_test_split(test_size=0.1)

    print(f"Dataset listo. Ejemplos de entrenamiento: {len(split_dataset['train'])}, Ejemplos de validación: {len(split_dataset['test'])}")


    # --- 3. Configurar el Modelo y el Entrenador ---

    print("Configurando el modelo y el entrenador...")

    # Carga el modelo T5 base.
    # Esto descarga el modelo (ej. t5-small) de Hugging Face.
    model = T5ForConditionalGeneration.from_pretrained(MODELO_BASE)

    # Define los argumentos (parámetros) para el entrenamiento
    training_args = Seq2SeqTrainingArguments(
        output_dir=CARPETA_MODELO_FINAL,
        num_train_epochs=3, 
        weight_decay=0.1, 
        
        fp16=True, 
        per_device_train_batch_size=12, 
        per_device_eval_batch_size=12,
        gradient_accumulation_steps=4, 

        dataloader_num_workers=4,
        
        warmup_steps=500,
        logging_dir="./logs",
        logging_steps=100,
        
        # --- CAMBIOS CORREGIDOS Y REQUERIDOS POR EL ERROR ---
        eval_strategy="steps",      # MANTENER: Queremos que evalúe por pasos
        save_strategy="steps",      # ⬅️ CORRECCIÓN: DEBE COINCIDIR con eval_strategy
        save_steps=200,             # MANTENER: Guarda un checkpoint cada 200 pasos
        save_total_limit=1,         # ⬅️ NUEVO: SOLO MANTIENE 1 CHECKPOINT. Esto evita que el disco se llene.
        # ----------------------------------------------------
        
        load_best_model_at_end=True, # ESTO AHORA FUNCIONARÁ
        predict_with_generate=True,
    )

    # El Data Collator se asegura de que las entradas y salidas
    # tengan el formato correcto durante el entrenamiento.
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer, 
        model=model
    )

    # Crea el "Entrenador" (Trainer)
    # Este es el "motor" que junta el modelo, los datos y los argumentos.
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=split_dataset["train"],      # Tu dataset de entrenamiento
        eval_dataset=split_dataset["test"],        # Tu dataset de validación
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    # --- 4. Iniciar el Entrenamiento ---

    print("¡¡Iniciando el entrenamiento!! 🚀")
    print("Esto puede tardar un tiempo (minutos u horas, dependiendo de tu PC)...")

    trainer.train()

    # --- 5. Guardar el Modelo Final ---

    print("Entrenamiento completado. Guardando el modelo final...")
    trainer.save_model(CARPETA_MODELO_FINAL)
    tokenizer.save_pretrained(CARPETA_MODELO_FINAL)
    print(f"¡Modelo guardado exitosamente en la carpeta: {CARPETA_MODELO_FINAL}")