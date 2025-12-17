# HCA spreadsheet Templates

Here are all the available templates using the latest [HCA metadata schema](https://github.com/HumanCellAtlas/metadata-schema/tree/master/json_schema). 
- [HCA template](hca_template.xlsx) - comprises all fields developed before tier 2 + GDN, as a more light generic template
- [Full template](hca_full_template.xlsx) - comprises all fields available in the latest [HCA metadata schema](https://github.com/HumanCellAtlas/metadata-schema/tree/master/json_schema). 
- [Lung template](hca_lung_template.xlsx) - with lung tier 2 fields + GDN
- [Gut template](hca_gut_template.xlsx) - with gut tier 2 fields + GDN


## Additional fields in specific bionetworks:
<details><summary>Lung specific</summary>


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

