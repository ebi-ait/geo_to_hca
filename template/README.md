# HCA spreadsheet Templates

Here are all the available templates using the latest [HCA metadata schema](https://github.com/HumanCellAtlas/metadata-schema/tree/master/json_schema). 
- [HCA template](hca_template.xlsx)
- [HCA template contributor](hca_template_contributor.xlsx)
    A minimised version of the full [HCA template](hca_template.xlsx) that is focused on the most common experimental design (no cell_line/ organoid no spatial trascriptomics, see more detail in the section [Tabs in contributor version](#tabs-in-contributor-version)) 

In order to deliver different biological networks needs, we also provide templates specific for each bionetwork with some fields that will be used exclusivly for the bionetwork.

- [Lung template](hca_lung_template.xlsx)


## Tabs in contributor version
<details><summary>HCA template contributor</summary>

**Tabs kept**:
	Project
	/ Project - Contributors
	/ Project - Publications
	/ Project - Funders
	/ Donor organism
	/ Specimen from organism
	/ Cell suspension
	/ Supplementary file
	/ Sequence file
	/ Analysis file
	/ Collection protocol
	/ Dissociation protocol
	/ Enrichment protocol
	/ Library preparation protocol
	/ Sequencing protocol
	/ Analysis protocol

**Tabs removed**
:
	~Organoid~
	/ ~Cell line~
	/ ~Imaged Specimen~
	/ ~Image file~
	/ ~Treatment protocol~
	/ ~Differentiation protocol~
	/ ~Aggregate generation protocol~
	/ ~Ipsc induction protocol~
	/ ~Imaging preparation protocol~
	/ ~Imaging protocol~
	/ ~Additional reagents~
	/ ~Imaging protocol - Channel~
	/ ~Imaging protocol - Probe~
	/ ~Familial relationship~

</details>

## Additional fields in specific bionetworks:
<details><summary>Lung template</summary>


| Programmatic name | schema | field | 
| ----------------- | ------ | ----- |
| `donor_organism.medical_tests.pft_method` | donor_organism.medical_tests | pft_method |
| `donor_organism.medical_tests.pft_age` | donor_organism.medical_tests | pft_age |
| `donor_organism.medical_tests.pft_time_point` | donor_organism.medical_tests | pft_time_point |
| `donor_organism.medical_tests.pft_relative_time_point` | donor_organism.medical_tests | pft_relative_time_point |
| `donor_organism.medical_tests.fev1_predicted` | donor_organism.medical_tests | fev1_predicted |
| `donor_organism.medical_tests.fev1_prebd` | donor_organism.medical_tests | fev1_prebd |
| `donor_organism.medical_tests.fev1_postbd` | donor_organism.medical_tests | fev1_postbd |
| `donor_organism.medical_tests.fev1_prebd_predicted_percent` | donor_organism.medical_tests | fev1_prebd_predicted_percent |
| `donor_organism.medical_tests.fev1_postbd_predicted_percent` | donor_organism.medical_tests | fev1_postbd_predicted_percent |
| `donor_organism.medical_tests.fvc_predicted` | donor_organism.medical_tests | fvc_predicted |
| `donor_organism.medical_tests.fvc_prebd` | donor_organism.medical_tests | fvc_prebd |
| `donor_organism.medical_tests.fvc_postbd` | donor_organism.medical_tests | fvc_postbd |
| `donor_organism.medical_tests.fvc_prebd_predicted_percent` | donor_organism.medical_tests | fvc_prebd_predicted_percent |
| `donor_organism.medical_tests.fvc_postbd_predicted_percent` | donor_organism.medical_tests | fvc_postbd_predicted_percent |
| `donor_organism.medical_tests.fev1_fvc_ratio_prebd` | donor_organism.medical_tests | fev1_fvc_ratio_prebd |
| `donor_organism.medical_tests.fev1_fvc_ratio_postbd` | donor_organism.medical_tests | fev1_fvc_ratio_postbd |
| `donor_organism.medical_tests.frc_abs` | donor_organism.medical_tests | frc_abs |
| `donor_organism.medical_tests.frc_predicted_percent` | donor_organism.medical_tests | frc_predicted_percent |
| `donor_organism.medical_tests.rv` | donor_organism.medical_tests | rv |
| `donor_organism.medical_tests.rv_predicted_percent` | donor_organism.medical_tests | rv_predicted_percent |
| `donor_organism.medical_tests.ic` | donor_organism.medical_tests | ic |
| `donor_organism.medical_tests.ic_predicted_percent` | donor_organism.medical_tests | ic_predicted_percent |
| `donor_organism.medical_tests.dlco` | donor_organism.medical_tests | dlco |
| `donor_organism.medical_tests.dlco_predicted_percent` | donor_organism.medical_tests | dlco_predicted_percent |
| `donor_organism.medical_tests.kco` | donor_organism.medical_tests | kco |
| `donor_organism.medical_tests.kco_predicted_percent` | donor_organism.medical_tests | kco_predicted_percent |
| `donor_organism.disease_profile.copd_gold_stage` | donor_organism.disease_profile | copd_gold_stage |
| `donor_organism.disease_profile.copd_mmrc_grade` | donor_organism.disease_profile | copd_mmrc_grade |
| `donor_organism.disease_profile.copd_cat_score` | donor_organism.disease_profile | copd_cat_score |
| `donor_organism.disease_profile.copd_gold_abe_assessment` | donor_organism.disease_profile | copd_gold_abe_assessment |
| `donor_organism.disease_profile.copd_phenotype` | donor_organism.disease_profile | copd_phenotype |
| `donor_organism.disease_profile.copd_emphysema_percentage` | donor_organism.disease_profile | copd_emphysema_percentage |

</details>