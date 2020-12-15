// Function to get the sushi url from the backend results
const sushiUrl = (data, sushiName) => {
  return data.classes?.filter(sushi => sushi.en === sushiName)[0].url;
};

// Some functions to manage image picking
const showPicker = () => {
  document.getElementById("file-input").click();
}
const showPicked = (event) => {
  document.getElementById("upload-label").innerHTML = event.currentTarget.files[0].name;
  const reader = new FileReader();
  reader.onload = function(e) {
    document.getElementById("image-picked").src = e.target.result;
    document.getElementById("image-picked").className = "";
  };
  reader.readAsDataURL(event.currentTarget.files[0]);
}

// Function run when click on the "Analyze" button
const analyze = () => {
  // Upload the selected images and raise an alert if none selected
  const uploadFiles = document.getElementById("file-input").files;
  if (uploadFiles.length !== 1) alert("Please select a file to analyze!");

  // Change the button text during analysis
  document.getElementById("analyze-button").innerHTML = "Analyzing...";

  // Create the formData (wrapping to send the image in a http POST request)
  const formdata = new FormData();
  formdata.append("file", uploadFiles[0]);

  const requestOptions = {
    method: 'POST',
    body: formdata
  };

  // In order to work locally and on the web, dynamically retrieve the POST url
  // Local will be: http://localhost:5000/analyze
  // Web might be: https://yanns-ai.onrender.com/analyze
  const loc = window.location;
  fetch(`${loc.protocol}//${loc.hostname}:${loc.port}/analyze`, requestOptions)
    .then(response => response.json())
    .then(data => {
      window.mydata = data;
      // Get the image classification result data from the backend (model)
      // Display it inside the "result" div.
      document.getElementById("result").innerHTML =
        `
          <h2>
            ${data.resultPct >= 60 ? `That's... a <a href="${sushiUrl(data, data.result)}">${data.result[0].toUpperCase()}${data.result.substring(1)}</a> sushi!` : `Not sure about that one... maybe a ${data.result} sushi?`}
          </h2>
          <p>Full result:</p>
          <ul>
          ${Object.keys(data.details)
            .filter(key => data.details[key] >= 5)
            .sort((keyA, keyB) => data.details[keyB] - data.details[keyA])
            .map(key =>
              `<li><a href="${sushiUrl(data,key)}">${key[0].toUpperCase()}${key.substring(1)}</a> sushi - ${data.details[key]}%</li>`)
            .join('')}
          </ul>
        `;
      // Change back the button text
      document.getElementById("analyze-button").innerHTML = "Analyze";
    })
    .catch(error => console.log('error',error));
}

// Event listeners
document.querySelector('.choose-file-button').addEventListener('click', showPicker);
document.querySelector('.analyze-button').addEventListener('click', analyze);
document.querySelector('#file-input').addEventListener('change', showPicked);



