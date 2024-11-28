async function uploadImage() {
    const input = document.getElementById('imageInput');
    const formData = new FormData();
    formData.append('file', input.files[0]);

    try {
        const response = await fetch('/upload', { method: 'POST', body: formData });
        const result = await response.json();

        if (result.status === 'success') {
            const data = result.data;

            // Update HTML with extracted data
            document.getElementById('medicine-name').textContent = data.name;
            document.getElementById('medicine-manufacturer').textContent = data.manufacturer;
            document.getElementById('medicine-composition').textContent = data.composition;
            document.getElementById('medicine-expiry-date').textContent = data.expiry_date;
            document.getElementById('medicine-batch').textContent = data.batch_number;
            document.getElementById('medicine-price').textContent = data.price;
            document.getElementById('medicine-warnings').textContent = data.warnings;
            document.getElementById('medicine-storage').textContent = data.storage_instructions;
        } else {
            alert(`Error: ${result.message}`);
        }
    } catch (error) {
        console.error('Error uploading image:', error);
    }
}
