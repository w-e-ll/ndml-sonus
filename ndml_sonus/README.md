
## Old crontab

```bash
5 2 * * *  /home/marvin/scripts/ndml-sonus/ndml_sonus/bin/getdata_production_marais.sh;\
           /home/marvin/scripts/ndml-sonus/ndml_sonus/bin/parsedata_production_marais.sh

10 2 * * * /home/marvin/scripts/ndml-sonus/ndml_sonus/bin/getdata_production_paille.sh;\
           /home/marvin/scripts/ndml-sonus/ndml_sonus/bin/parsedata_production_paille.sh

          
15 0 * * * /home/marvin/scripts/ndml-sonus/ndml_sonus/bin/getdata_production_psx.sh;\
           /home/marvin/scripts/ndml-sonus/ndml_sonus/bin/parsedata_production_psx.sh;\
           /home/marvin/scripts/ndml-sonus/ndml_sonus/loader_generic/bin/copy_and_load_prod.sh;\
           /home/marvin/scripts/ndml-sonus/ndml_sonus/loader_generic/bin/copy_and_load_uat.sh
```
