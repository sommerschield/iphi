# I.PHI dataset: ancient Greek inscriptions

Thea Sommerschield<sup>\*</sup>, Yannis Assael<sup>\*</sup>, Brendan Shillingford, Mahyar Bordbar, John Pavlopoulos, Marita Chatzipanagiotou, Ion Androutsopoulos, Jonathan Prag, Nando de Freitas

---

Χαῖρε! This repository is forked from [Pythia](https://github.com/sommerschield/ancient-text-restoration), and contains a pipeline to download and process the [Packard Humanities Institute](https://inscriptions.packhum.org/) database of ancient Greek inscriptions including the geographical and chronological metadata into a machine actionable format. The processed dataset is referred to as I.PHI.


## Dependencies
```
pip install -r requirements.txt && \
python -m nltk.downloader punkt
```

## Dataset generation
```
# Download and process PHI (this will take a while)
python -m train.data.iphi_download  --connections=1
```

To enable multi-threaded processing set: `--connections=100`.

Preprocessed I.PHI dataset uploaded by @Holger.Danske800: [link](https://drive.google.com/drive/folders/1WupkpBTP7BTGTqAwKQ8BSFrCaQTbKX9c)

## Reference
When using this dataset, please cite the [Packard Humanities Institute](https://inscriptions.packhum.org/) database of ancient Greek inscriptions and:
```
@misc{sommerschield2021iphi,
  title={{I.PHI} dataset: ancient Greek inscriptions},
  author={Sommerschield*, Thea and Assael*, Yannis and Shillingford, Brendan and Bordbar, Mahyar and Pavlopoulos, John and Chatzipanagiotou, Marita and Androutsopoulos, Ion and Prag, Jonathan and de Freitas, Nando},
  howpublished = {\url{https://github.com/sommerschield/iphi}},
  year={2021}
}
```

## License
Apache License, Version 2.0

<p align="center">
<img alt="Epigraphy" src="http://yannisassael.com/projects/pythia/epigraphy_transp.png" width="256" /><br />
Damaged inscription: a decree concerning the Acropolis of Athens (485/4 BCE). <it>IG</it> I<sup>3</sup> 4B.<br />(CC BY-SA 3.0, WikiMedia)
</p>
