# API Reference

## POST `/api/brief/by-citation`

Generate or fetch a PDF case brief by citation.

**Parameters (form-data)**  
- `citation` (string, required): e.g. `384 U.S. 436`  
- `mode` (string, optional, default: `professional`): `professional` or `student`  
- `fmt` (string, required, must be `pdf`)

**Response**  
- `200 OK`: Returns the PDF file.  
- `400 Bad Request`: Missing or invalid parameters.  
- `500 Internal Server Error`: Pipeline failure.  
- `404 Not Found`: No existing PDF for that case.

## CLI

```bash
python pipeline.py --case "384 U.S. 436" --mode professional --format pdf
```