## Installation

Add the following to `.env` file

```
ENV='prod/dev'
PLATFORM='win/linux'
SECRET_KEY='some-key'
HOST='http://127.0.0.1:3000'

# smtp variables
EMAIL_DOMAIN='smtp.<domaon>.com'
EMAIL_ADDRESS='admin.iee@winvinaya.com'
EMAIL_PASSWORD='<your-password>'

# DB variables
DB_HOST = 'localhost'
DB_USER = 'winvinaya_iee'
DB_PASSWORD = 'password'
DB_NAME = 'invoice_extraction'
DB_PORT = 3306

# Invoice variables
CREDITS_VALUE = 2
CREDITS_PER_PAGE = 5
```

## Notes

#Step 1: text cleaning # special charecters, puntucations marks, charecter symbols,
#Step 2: Tokenization # Split the text into individual tokens, such as words or numbers.
#Step 3: Normalization # Convert tokens to a standard format such as lowercase.
#Step 4: Date_standardization # Extract and standardize date formats from the invoice to (dd-mm-yyy).

            text_clean(invoice)
                # remove non alpha numeric charecteres
                # remove extra white spaces
                # include dots

            text_tokenizer(output1)
                # split text into individual tokens

            text_normalization(output2)
                # convert text to lower case

            date_standardization(output3)
                # convert dates to standarded format (dd/mm/yyyy)


            for invoice in invoice_ocr folder(index)
                output1 = text_clean (invoice)
                output2 = text_tokenizer(output1)
                output3 = text_normalization(output2)
                output4 = date_standardization(output3)
                # save final output to final_text_annotations.txt
                # array of strings - Tokanization output
                # index - final_text_annotations{index}.txt

### image processing

    # step1: grayscale convertion
    # step2: Noise reduction or removal (blur, smoothing techniques)
    # step3: image enhancement (contrast, sharpness)
    # step4: adaptive thresholding
    # step5: rotations corrections
    # step6: deskewing
    # step7: background subtraction
    # step8: text edge enhancement
    # step9: colour space transformation
    # step10: Morphological Operations (erosion and dilation)

### Install MM detection

```
conda create --name openmmlab python=3.8 -y
conda activate openmmlab
conda install pytorch torchvision -c pytorch
pip install -U openmim
mim install mmengine
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
mim install "git+https://github.com/open-mmlab/mmcv.git@6299bc02bde35f96e0b57a6cc94ed0fda177c478"
mim install mmdet
```

For Testing, run

```
from mmdet.apis import init_detector, inference_detector

config_file = 'rtmdet_tiny_8xb32-300e_coco.py'
checkpoint_file = 'rtmdet_tiny_8xb32-300e_coco_20220902_112414-78e30dcc.pth'
model = init_detector(config_file, checkpoint_file, device='cuda:0')
inference_detector(model, 'demo/demo.jpg')
```

#References

1. https://github.com/open-mmlab/mmdetection/issues/6765#issuecomment-1768507085
2. https://medium.com/swlh/ocr-engine-comparison-tesseract-vs-easyocr-729be893d3ae
