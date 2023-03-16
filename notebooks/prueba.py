import pandas as pd
import numpy as np
import vaex

traf = vaex.open('../../TRAFICO/traf_hist_unir.hdf5')

#read acci_filtered_vaex

acci_filtered_vaex = vaex.open('../../acci_filtered_vaex.hdf5')
acci_fil = acci_filtered_vaex[['idelem', 'lesividad']]
#from vaex to pandas

acci_fil = acci_fil.to_pandas_df()
#drop duplicates by idelem

acci_fil = acci_fil.drop_duplicates(subset='idelem', keep='first')
#acci_fil to vaex

acci_fil_vaex = vaex.from_pandas(acci_fil)
#left join acci_fil with traf

traf_acci = traf.join(acci_fil_vaex, on='idelem', how='left')
#drop missing in lesividad column

traf_acci2 = traf_acci.dropmissing(column_names=['lesividad'])
#drop lesividad column

traf_acci2 = traf_acci2.drop(['lesividad'])
#read acci_filtered_vaex

acci_filtered_vaex = vaex.open('../../acci_filtered_vaex.hdf5')
# to pandas

acci = acci_filtered_vaex.to_pandas_df()
acci['accidente']  = 1
#rename idelem to id

acci.rename(columns={'idelem': 'id'}, inplace=True)

#filter accis by id equal to diff

acci = acci[['fecha', 'hora', 'id', 'accidente']]

#add 0 to the left of hora if length is 4

for i in range(len(acci)):
    if len(acci['hora'][i]) == 4:
        acci['hora'][i] = '0' + acci['hora'][i]

#acci to vaex

acci_vaex = vaex.from_pandas(acci)

acci_vaex['unir'] = acci_vaex['fecha'] + ' ' + acci_vaex['hora'] + ':00' + ' ' + acci_vaex['id']
acci_vaex = acci_vaex.drop(['fecha','hora','id'])

#group by unir and sum

acci_vaex = acci_vaex.groupby('unir', agg={'accidente':'sum'})

#join traf_acci2 with acci_vaex

traf_acci3 = traf_acci2.join(acci_vaex, on='unir', how='left')
traf_acci3 = traf_acci3.drop(['unir'])

print('done')