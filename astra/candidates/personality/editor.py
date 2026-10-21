"""Explicit offline editor. No model calls; defaults to a separate local DB."""
from pathlib import Path
import json,sys,uuid
sys.path.insert(0,str(Path(__file__).resolve().parent))
from personality import PersonalityStore,TRAITS,SCOPES,prepare_messages
from baseline import worksheet

def main(*,database_path=None,on_ready=None):
    import tkinter as tk
    from tkinter import ttk,messagebox,filedialog
    store=PersonalityStore(database_path or Path(__file__).with_name('calibration.sqlite'))
    root=tk.Tk();root.title('Astra personality calibration — offline candidate')
    root.geometry('880x780');root.minsize(880,780);status=tk.StringVar();version=None;scales={}
    ttk.Label(root,text='Start from an unpersonalized baseline. Local prompt calibration only—not fine-tuned weights.',wraplength=840).pack(pady=8)
    panel=ttk.Frame(root);panel.pack(fill='x',padx=12)
    for key in TRAITS:
        row=ttk.Frame(panel);row.pack(fill='x');ttk.Label(row,text=key.title(),width=15).pack(side='left')
        value=tk.IntVar(value=2);scales[key]=value
        tk.Scale(row,from_=0,to=4,orient='horizontal',variable=value,length=400).pack(side='left')
    ttk.Label(root,text='Feedback examples (JSON). Edit prompt/preferred/reason; reviewed=false keeps examples out of previews.',wraplength=840).pack()
    examples=tk.Text(root,height=13,wrap='word');examples.pack(fill='both',expand=True,padx=12)
    bar=ttk.Frame(root);bar.pack(fill='x',padx=12,pady=5)
    query=tk.StringVar(value='How can we make this explanation clearer?');scope=tk.StringVar(value='general')
    ttk.Entry(root,textvariable=query).pack(fill='x',padx=12)
    options=ttk.Frame(root);options.pack(fill='x',padx=12)
    ttk.Combobox(options,textvariable=scope,values=SCOPES,state='readonly',width=15).pack(side='left')
    mood=tk.StringVar(value='neutral');ttk.Combobox(options,textvariable=mood,values=('neutral','gentle','playful','focused'),state='readonly',width=15).pack(side='left')
    output=tk.Text(root,height=9,wrap='word');output.pack(fill='both',expand=True,padx=12)
    ttk.Label(root,textvariable=status,wraplength=840).pack()
    ttk.Button(root,text='Baseline worksheet (no assumed answers)',command=lambda:show(json.dumps(worksheet(),ensure_ascii=False,indent=2))).pack()
    def show(value):output.delete('1.0','end');output.insert('1.0',value)
    def load():
        nonlocal version
        version,state=store.current()
        for k,v in state['traits'].items():scales[k].set(v)
        examples.delete('1.0','end');examples.insert('1.0',json.dumps(state['examples'],ensure_ascii=False,indent=2))
        status.set(f'Local version {version}; no live integration or model training')
    def guarded(fn):
        def run():
            try:fn()
            except Exception as exc:messagebox.showerror('Calibration unchanged / action failed',str(exc))
        return run
    def save():
        store.save({'traits':{k:v.get() for k,v in scales.items()},'examples':json.loads(examples.get('1.0','end'))},expected_version=version);load()
    def add(vote):
        data=json.loads(examples.get('1.0','end'))
        data.append(dict(id=uuid.uuid4().hex,scope=scope.get(),kind='style',vote=vote,prompt='Write the relevant example prompt here',preferred='' if vote=='down' else 'Write your preferred response here',rejected='',reason='Explain what felt wrong' if vote=='down' else '',reviewed=False))
        examples.delete('1.0','end');examples.insert('1.0',json.dumps(data,ensure_ascii=False,indent=2))
        status.set('Unsaved example. Author preferred wording/reason and explicitly set reviewed=true when ready.')
    def undo():store.undo(expected_version=version);load()
    def reset():
        if messagebox.askyesno('Reset calibration','Reset this separate calibration to neutral defaults? Undo can restore it.'):
            store.reset(expected_version=version);load()
    def preview():
        store.set_mood(mood.get(),seconds=900)
        messages,receipt=prepare_messages([{'role':'system','content':'Synthetic preview identity: assistant Astra, user ExampleUser. No tools.'},{'role':'user','content':query.get()}],store,query.get(),scope.get())
        show(json.dumps({'meaning':'Context preview only; no response generated','receipt':receipt,'messages':messages},ensure_ascii=False,indent=2))
    def export():
        target=filedialog.asksaveasfilename(defaultextension='.json',title='Export saved local preferences (may contain your examples)')
        if target:
            with Path(target).open('x',encoding='utf-8') as f:f.write(store.export())
            status.set('Saved version exported locally; nothing uploaded')
    buttons={}
    for i,(label,fn) in enumerate([('Save version',save),('Add thumbs up',lambda:add('up')),('Add thumbs down',lambda:add('down')),('Undo',undo),('Reset',reset),('Export',export),('Preview saved context',preview)]):
        button=ttk.Button(bar,text=label,command=guarded(fn));button.grid(row=i//4,column=i%4,padx=3,pady=3,sticky='ew');buttons[label]=button
    for column in range(4):bar.columnconfigure(column,weight=1)
    def tab(event,back=False):
        target=event.widget.tk_focusPrev() if back else event.widget.tk_focusNext()
        target.focus_set();return 'break'
    for widget in (examples,output):
        widget.bind('<Tab>',tab);widget.bind('<Shift-Tab>',lambda event:tab(event,True))
    def dirty():
        try:return {'traits':{k:v.get() for k,v in scales.items()},'examples':json.loads(examples.get('1.0','end'))}!=store.current()[1]
        except (ValueError,TypeError):return True
    def close():
        if dirty() and not messagebox.askyesno('Unsaved calibration','Discard unsaved editor changes? Saved versions remain intact.'):return
        store.close();root.destroy()
    root.protocol('WM_DELETE_WINDOW',close);load()
    if on_ready:root.after(150,lambda:on_ready(dict(root=root,store=store,buttons=buttons,examples=examples,output=output,query=query,scales=scales,status=status,close=close)))
    root.mainloop()

if __name__=='__main__':main()
