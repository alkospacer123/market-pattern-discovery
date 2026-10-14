"""Standalone research heatmap, signed CLOSED Gross R; no capital-return claim."""
import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from io_utils import read_csv,write_csv
def plot(out):
 ranks=[r for r in read_csv(out/'STABILITY_RANKING.csv') if r['mode']=='NEXT_OPEN']
 months=[f'{y}-{m:02d}' for y in (2023,2024,2025,2026) for m in range(1,13 if y<2026 else 11)]
 rows=[r for r in read_csv(out/'MONTHLY_COMPARISON.csv') if r['view']=='FULL_AVAILABLE' and r['instruments']=='USDRUBF;CNYRUBF;GLDRUBF;IMOEXF' and r['build_id'] in {q['build_id'] for q in ranks}]
 lookup={(r['build_id'],r['month']):r for r in rows};data=np.array([[float(lookup[r['build_id'],m]['gross_R']) if lookup[r['build_id'],m]['coverage']!='NO_COVERAGE' else np.nan for m in months] for r in ranks])
 labels=[r['build_id'].replace('A6_S1_NEXT_OPEN_','A6+S1 ').replace('T1_S1_NEXT_OPEN_','T1+S1 ').replace('T1_NEXT_OPEN_','T1 ').replace('TRAIL_3p0','TRAIL_300').replace('TRAIL_3p5','TRAIL_350').replace('A6_S1_EARLY_PROTECT_05_NEXT_OPEN_TRAIL_375','EARLY_PROTECT_05') for r in ranks]
 plt.rcParams['svg.hashsalt']='IntradayLabComparisonV1';fig,ax=plt.subplots(figsize=(20,6.4));cmap=plt.get_cmap('RdYlGn').copy();cmap.set_bad('#c7ccd3')
 limit=float(np.nanmax(abs(data)));im=ax.imshow(data,aspect='auto',cmap=cmap,vmin=-limit,vmax=limit)
 ax.set_yticks(range(len(labels)),labels,fontsize=8);ax.set_xticks(range(len(months)),[m[2:] for m in months],rotation=90,fontsize=7)
 ax.set_title('Frozen NEXT_OPEN builds, N4: monthly CLOSED Gross R | POST_HOC_COMPARISON',fontsize=13,pad=14)
 for i in range(len(labels)):
  for j,m in enumerate(months):
   if not np.isnan(data[i,j]):ax.text(j,i,f'{data[i,j]:.0f}',ha='center',va='center',fontsize=6,color='#17202b')
   if m in ('2026-08','2026-09'):ax.add_patch(Rectangle((j-.5,i-.5),1,1,fill=False,edgecolor='#434e66',linewidth=.7,linestyle='--'))
 for j in (11.5,23.5,35.5):ax.axvline(j,color='#263348',linewidth=1.5)
 cb=fig.colorbar(im,ax=ax,pad=.012,shrink=.8);cb.set_label('Gross R, descriptive pooled',fontsize=9)
 fig.text(.13,.018,'Grey = NO_COVERAGE. Dashed cells = incomplete Aug/Sep 2026. Calendar cutoff: 2026-10-13 00:00 MSK, exclusive.\nClosed R is not deposit return; source gaps and late 2023 starts remain in the CSV coverage tables.',fontsize=8)
 fig.subplots_adjust(left=.20,right=.94,bottom=.18,top=.89)
 fig.savefig(out/'MONTHLY_HEATMAP.svg',metadata={'Date':None});fig.savefig(out/'MONTHLY_HEATMAP.png',dpi=120);plt.close(fig)
 write_csv(out/'PLOT_DATA.csv',[dict(build_id=r['build_id'],month=r['month'],gross_R=r['gross_R'],coverage=r['coverage']) for r in rows])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();plot(a.output)
