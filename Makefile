MAILDIFF_TARGET := maildiff


lambda: clean
	@mkdir -p $(MAILDIFF_TARGET)
	@cp *.py $(MAILDIFF_TARGET)/
	@cp *.json $(MAILDIFF_TARGET)/
	@pip3 install -r requirements.txt -t $(MAILDIFF_TARGET)
	@pushd $(MAILDIFF_TARGET) && zip -r ../maildiff.zip * && popd
	@rm -rf $(MAILDIFF_TARGET)

clean:
	-@rm -rf $(MAILDIFF_TARGET)
	-@rm -f maildiff.zip

run: venv
	venv/bin/python maildiff.py

venv:
	@python3 -m venv venv
	@venv/bin/pip install -r requirements.txt
