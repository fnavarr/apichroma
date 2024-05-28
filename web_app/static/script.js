document.addEventListener('DOMContentLoaded', () => {

    const uploadForm = document.getElementById('upload-form');
    // console.log("uploadform: " + uploadForm)

    // NOTA.
    // El siguiete codigo no sera ejecutado en el cliente.
    // La función de carga se implemantará en el servidor como 
    // una fincion del administrador. Se deja aqui unicamente como 
    // referencia inicial.
    
    if (uploadForm) {
        // Obtener el input de archivo y el div donde se mostrará la información
        const fileInput = document.getElementById('fileInput');
        const fileDetails = document.getElementById('fileDetails');

        // Agregar un evento para cuando se seleccione un archivo
        fileInput.addEventListener('change', (event) => {
            const file = event.target.files[0];

            if (file) {
                const myFile = file.name
                // Mostrar información del archivo seleccionado
                const fileInfo = `
                    Nombre del archivo: ${file.name} <br>
                    Tamaño del archivo: ${(file.size / 1024).toFixed(2)} KB <br>
                    Tipo de archivo: ${file.type}
                `;
                fileDetails.innerHTML = fileInfo;
            } else {
                myFile = "vacio"
                fileDetails.innerHTML = 'No se ha seleccionado ningún archivo.';
            }
        });


        uploadForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            //alert("Oprimí submit")
            
            const fileInput = document.getElementById('fileInput').files[0].name;

            var result = {fileInput};

            formData = JSON.stringify(result)
            console.log("Result: " + formData)

            const response = await fetch('http://localhost:8000/upload_pdfs', {
                method: 'POST', 
                headers: {
                    "Content-type": "application/json; charset=UTF-8" 
                },
                body: JSON.stringify({ result })
            });

            const data = await response.json();
            const uploadStatus = document.getElementById('upload-status');
            uploadStatus.textContent = data.message || data.error;
        });
    }

    const form = document.getElementById('question-form');
    // console.log("form: " + form)
    if (form) {
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            
            const question = document.getElementById('question').value;

            const response = await fetch('http://34.212.146.55:8000/query', {
                method: 'POST', 
                headers: {
                    "Content-type": "application/json; charset=UTF-8" 
                },
                body: JSON.stringify({ question })
            });
            // console.log("Que hay en question: " + question);
            
            const data = await response.json();
            displayResults(question, data);

        });

        const fetchFileList = async () => {
            const response = await fetch('http://34.212.146.55:8000/list_files', {method: 'GET'});
            const data = await response.json();
            displayFileList(data);
        };

        const displayFileList = (files) => {
            const fileList = document.getElementById('file-list'); // obtiene el elemento donde se agregaran los li
            fileList.innerHTML = '';

            const data = JSON.parse(files); // convierte JSON del API a objeto JavaScrip
            const arrayFiles = data.files;  // crea el rarreglo 
            
            // Itera el arreglo para obtener la lista y crea elementos li
            arrayFiles.forEach(file => {
                    const listItem = document.createElement('li');
                    listItem.textContent = file;
                    fileList.appendChild(listItem);
                });
        };

        fetchFileList();
    }
});

function displayResults(question, data) {
    const dataStr = JSON.stringify(data); 
    console.log("===>>> Esto tiene dataStr: " + dataStr)

    // Convertir el JSON a un objeto JavaScript
    const dataX = JSON.parse(dataStr);

    // Obtener el contenido de la respuesta
    const answer = dataX.answer;

    // Crear un elemento h3 para la respuesta
    const answerElement = document.createElement('h3');
    answerElement.textContent = "Respuesta a: " + question;

      // Crear un elemento p para el texto de la respuesta
    const answerText = document.createElement('p');
    answerText.textContent = answer;
   

    // Obtener el div donde se agregará el contenido
    const contentDiv = document.getElementById('results');

    // Agregar los elementos al div
    contentDiv.appendChild(answerElement);
    contentDiv.appendChild(answerText);

}
