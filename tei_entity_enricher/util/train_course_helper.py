import streamlit as st
import pandas as pd
import altair as alt

c_epoch = "Epoch"
c_ef1 = "E-F1-Score"
c_loss = "Loss"

def extract_metric_from_string(metric_name,metrics_string):
    metric_start_index=metrics_string.find(metric_name)
    if metric_start_index>=0:
        extracted_metric_start=metrics_string[metric_start_index+len(metric_name)+1:]
        metric_end_index=extracted_metric_start.find("-")
        if metric_end_index>=0:
            metric_value = extracted_metric_start[:metric_end_index].replace(" ","")
        else:
            metric_value = extracted_metric_start.replace(" ","")
        try:
            float_metric_value=float(metric_value)
            return float_metric_value
        except ValueError:
            return None
    return None



def extract_val_metrics_from_train_log(filepath):
    with open(filepath) as f:
        lines=f.readlines()
    metrics=[]
    for line in lines:
        result_start_index=line.find("Results of epoch")
        if result_start_index>=0:
            try:
                epoch=int(line[result_start_index+len("Results of epoch"):result_start_index+len("Results of epoch")+5].replace(" ",""))
                extracted_metric_line=line[result_start_index+len("Results of epoch")+5:]
                ef1=extract_metric_from_string("val_SeqEvalF1FixRule",extracted_metric_line)
                loss=extract_metric_from_string("val_loss",extracted_metric_line)
                if ef1 is not None or loss is not None:
                    metrics.append({c_epoch:epoch,c_ef1:ef1,c_loss:loss})
            except ValueError:
                pass
    return metrics

def show_metric_line_chart(metrics,metric_name):
    epochlist=[]
    epoch_to_value_dict={}
    for metric in metrics:
        if metric_name in metric.keys() and metric[metric_name] is not None:
            epochlist.append(metric[c_epoch])
            epoch_to_value_dict[metric[c_epoch]]=metric[metric_name]
    epochlist.sort()
    valuelist=[epoch_to_value_dict[epoch] for epoch in epochlist]
    alt_chart_data=pd.DataFrame({
      c_epoch: epochlist,
      metric_name: valuelist
    })
    min_value=min(valuelist)
    max_value=max(valuelist)
    min_scale=min_value-0.1*(max_value-min_value)
    max_scale=max_value+0.1*(max_value-min_value)
    alt_chart=alt.Chart(alt_chart_data).mark_line().encode(
        x=c_epoch,
        y=alt.Y(metric_name,scale=alt.Scale(domain=[min_scale,max_scale]))
    )
    st.altair_chart(alt_chart)
