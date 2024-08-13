# HCA spreadsheet Templates

Here are all the available templates using the latest [HCA metadata schema](https://github.com/HumanCellAtlas/metadata-schema/tree/master/json_schema). 
- [HCA template](hca_template.xlsx)

In order to deliver different biological networks needs, we also provide templates specific for each bionetwork with some fields that will be used exclusivly for the bionetwork.

- [Lung template](hca_lung_template.xlsx)


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

</details>