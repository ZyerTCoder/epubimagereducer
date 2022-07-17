$py = "C:\Users\AZM\Documents\Python\epubimagereducer\epubimagereducer.py"
foreach ($i in Get-ChildItem "C:\Users\AZM\Documents\LNs\todo"){
	python $py $i.FullName
	ebook-convert $i.name ($i.name.substring(0, $i.name.length-5)+"c.epub")
}
