14/02/25

────────────────────────── Traceback (most recent call last) ───────────────────────────
  /home/central/Documents/thermal_env/lib/python3.13/site-packages/streamlit/runtime/s  
  criptrunner/exec_code.py:129 in exec_func_with_error_handling                         
                                                                                        
  /home/central/Documents/thermal_env/lib/python3.13/site-packages/streamlit/runtime/s  
  criptrunner/script_runner.py:669 in code_to_exec                                      
                                                                                        
  /home/central/Documents/thermal_env/lib/python3.13/site-packages/streamlit/runtime/s  
  criptrunner/script_runner.py:165 in _mpa_v1                                           
                                                                                        
  /home/central/Documents/thermal_env/lib/python3.13/site-packages/streamlit/navigatio  
  n/page.py:310 in run                                                                  
                                                                                        
  /home/central/Documents/sensors_to_HA/data_handler/streamlit_app.py:91 in <module>    
                                                                                        
    88                                                                                  
    89                                                                                  
    90 if __name__ == "__main__":                                                       
  ❱ 91 │   main()                                                                       
    92                                                                                  
                                                                                        
  /home/central/Documents/sensors_to_HA/data_handler/streamlit_app.py:83 in main        
                                                                                        
    80 │   │   if page == "Live Metrics":                                               
    81 │   │   │   render_live_metrics(snapshot, table_placeholder, raw_placeholder)    
    82 │   │   elif page == "Adaptive Multi-User":                                      
  ❱ 83 │   │   │   render_multi_user_comfort(snapshot, multi_user_placeholder)          
    84 │   │   else:                                                                    
    85 │   │   │   render_llm_assistant(question, ask_button, sensor_box, user_box, ll  
    86                                                                                  
                                                                                        
  /home/central/Documents/sensors_to_HA/data_handler/pages/multi_user_comfort.py:35 in  
  render_multi_user_comfort                                                             
                                                                                        
    32 │   │   │   return                                                               
    33 │   │                                                                            
    34 │   │   # 3. Calculate comfort for each user                                     
  ❱ 35 │   │   results = get_multi_user_results(env_reading, users)                     
    36 │   │                                                                            
    37 │   │   # Display ID as short UID in table                                       
    38 │   │   display_results = []                                                     
────────────────────────────────────────────────────────────────────────────────────────
NameError: name 'get_multi_user_results' is not defined


11/12/25

[Unit]
Description=Thermal AMG8833 MQTT Publisher
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=zerocluster
WorkingDirectory=/home/zerocluster/sensors_to_HA/AMG-8833-Grid-eye

ExecStart=/home/zerocluster/my_venv/bin/python \
  /home/zerocluster/sensors_to_HA/AMG-8833-Grid-eye/AMG-8833--MQTT.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target




---

sudo systemctl daemon-reload
sudo systemctl restart your-service-name.service


To debug:
sudo systemctl status your-service-name.service
sudo journalctl -u your-service-name.service -e

--
Run manually

sudo -u zerocluster /home/zerocluster/my_venv/bin/python \
  /home/zerocluster/sensors_to_HA/AMG-8833-Grid-eye/AMG-8833--MQTT.py



02/12/25
sudo minicom -D /dev/ttyACM0 -b 256000


01/12/25
venv 
thermal_env
